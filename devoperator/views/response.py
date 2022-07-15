import json
from multiprocessing import context
import os
from pathlib import Path
import random
from socket import timeout
from sre_constants import SUCCESS
import time
from datetime import datetime
import unicodedata
from celery import current_app
from django.dispatch import receiver
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from django.db import DatabaseError, transaction
from django.urls import reverse, resolve
from django.shortcuts import render
from datetime import datetime

from devoperator.tasks import run
from .common import HttpResponseBase, BasicJsonResponse, ParsedClientView
from xlsxwriter import Workbook
from crawler.models import Bloger
from devoperator.models import Ip, LoginSession, Message, NaverAccounts, NoteSendingLog, Quote
from http import cookiejar
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests.utils import requote_uri
from devoperator.utility.utility import accumulator, file_handle, generate_login_cookie, who_are_you
from django.contrib import messages
from util.ip_util import switchIp2, get_myip
from util.naver_note import Session
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from django.db.models import Q
from devoperator.utility.make_dir import create_dir
from django.contrib.auth.hashers import make_password, check_password


class CheckAccount(ParsedClientView):
    @ParsedClientView.init_parse
    def post(self, req):        
        data = json.loads(req.body.decode())                
        wtime = [i for i in range(2, 7)]                
        for id in data['ids']:
            switchIp2()
            time.sleep(random.choice(wtime))            
            acc = NaverAccounts.objects.get(id=id)
            check = Session(acc.nid, acc.npw)
            res = check.check_account()            
            if isinstance(res, str):
                return BasicJsonResponse(data={'id': id, "result": 'X'})
            else:
                return BasicJsonResponse(data={'id': id, "result": res})

class ExcelForm(ParsedClientView):
    @ParsedClientView.init_parse
    def get(self, req):                 
        today = datetime.now().strftime('%Y%m%d')
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        create_dir(f"{path}\\form")
        file_name = f"네이버_계정_형식_{today}.xlsx"
        wb = Workbook(f"{path}/form/{file_name}")
        ordered_list = ['아이디', '비밀번호']
        ws = wb.add_worksheet()
        first_row = 0
        for header in ordered_list:
            col = ordered_list.index(header)
            ws.write(first_row, col, header)        
        wb.close()                
        return BasicJsonResponse(data=file_name)
    

class SendNote(ParsedClientView):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data = {
            "data": [],
        }
    @ParsedClientView.init_parse
    @transaction.atomic
    @csrf_exempt
    def post(self, req):        
        data = json.loads(req.body.decode('utf-8'))
        acc_ids = data.get('accs') # 발신 계정들
        msg_ids = data.get('msg') # 메시지        
        receiver_ids = data.get('receiver') # 수신자        
        quote_ids = data.get('quote', '') # 명언 포함 여부                       
        if not acc_ids:
            return BasicJsonResponse(is_success=False, status=503, error_msg='선택된 계정이 없습니다.')
        if len(acc_ids) > 1:
            return BasicJsonResponse(is_success=False, status=503, error_msg='발신 계정은 한 개만 선택 해주세요')
        if not receiver_ids:
            return BasicJsonResponse(is_success=False, status=503, error_msg='선택된 수신자 아이디가 없습니다.')
        if msg_ids:
            msgs = Message.objects.filter(id__in=msg_ids).values()
        else:
            return BasicJsonResponse(is_success=False, status=503, error_msg='선택된 메세지가 없습니다.')
        if quote_ids:
            quotes = Quote.objects.filter(id__in=quote_ids).values()
        msgs = [f"{m['msg']}\n\n{q['msg']}" for m in msgs for q in quotes]        
        
        for acc_id in acc_ids:
            acc_inst = NaverAccounts.objects.get(id=acc_id)                       
            send_dict = {
                'uid': acc_inst.nid, 
                'upw': acc_inst.npw,
                'msg': random.choice(msgs),
                'receivers': [r_inst.nid for r_inst in Bloger.objects.filter(id__in=receiver_ids)]
            }
            run.delay(**send_dict)
            
        # try:
        #     NoteSendingLog.objects.bulk_create(bulk_list)
        # except DatabaseError as e:
        #     return BasicJsonResponse(is_success=False, status=503, error_msg=e)
        # return BasicJsonResponse(is_success=True, status=200)                
    
    def log_gen(self, log_qs):
            for l in log_qs:
                yield {                    
                    "log": f"계정:{l.account.nid}/ 발신자:{l.receiver.nid}/ 발신결과: {l.is_success if l.is_success else l.error_msg} 시간: {l.try_at}"
                    }
    @ParsedClientView.init_parse
    def get(self, req):             
        todate = datetime.now().strftime('%Y-%m-%d')        
        logs = NoteSendingLog.objects.select_related('account').select_related('ip').select_related('receiver').filter(try_at_date=todate)
        self.data["data"].extend(self.log_gen(logs))        
        return HttpResponse(json.dumps(self.data["data"]), content_type="application/json")
    

class AssignAccounts(ParsedClientView):
    @ParsedClientView.init_parse
    @transaction.atomic
    def post(self, req):        
        if req.FILES:
            excel_file = req.FILES['excelfile']            
            accs = self.file_handle(excel_file)
            
            bulk_list = []
            for d in accs:
                if not NaverAccounts.objects.filter(nid=d['nid']):
                    bulk_list.append(NaverAccounts(nid=d['nid'], npw=d['npw']))
                else:
                    continue
            try:
                NaverAccounts.objects.bulk_create(bulk_list)
            except DatabaseError as e:
                return BasicJsonResponse(is_success=False, status=503, error_msg=e)
            return BasicJsonResponse(is_success=True, status=200)
        
        else:            
            data = json.loads(req.body.decode('utf-8'))
            
            nid = data['nid']
            npw = data['npw']
            try:            
                NaverAccounts.objects.get(nid=nid)            
            except NaverAccounts.DoesNotExist:
                NaverAccounts(**data).save()
                return BasicJsonResponse(is_success=True, status=200,)            
            return BasicJsonResponse(is_success=False, status=503, error_msg='해당 계정이 이미 있습니다.')
            
    def file_handle(self, excel_file):        
        df = pd.read_excel(excel_file)
        df = pd.DataFrame(df).iterrows()
        data = []
        for index, row in df:            
            data.append({'nid': row['아이디'], 'npw': row['비밀번호']})
        return data 

    @ParsedClientView.init_parse
    def get(self, req):                
        return BasicJsonResponse(data=NaverAccounts.objects.all())



class AddMsg(ParsedClientView):
    model = Message

    @ParsedClientView.init_parse
    @transaction.atomic 
    def post(self, req):         
        if req.FILES:
            excel_file = req.FILES['excelfile']
            msgs = self.file_handle(excel_file)
            bulk_list = []
            for m in msgs:
                if self.model.objects.filter(msg__in=m['msg']):
                    continue
                else:
                    bulk_list.append(self.model(msg=m['msg']))
            try:
                self.model.objects.bulk_create(bulk_list)
            except DatabaseError as e:
                return BasicJsonResponse(is_success=False, status=503, error_msg=e)
            return BasicJsonResponse(is_success=True, status=200)

        else:
            data = json.loads(req.body.decode('utf-8'))
            msg = data['msg']        
            try:
                l = self.model.objects.get(msg=msg)                
            except self.model.DoesNotExist:
                self.model(**data).save()
                return BasicJsonResponse(
                    is_success=True,
                    status=200,)
            else:
                return BasicJsonResponse(                    
                    status=503, error_msg='해당 명언이 이미 존재합니다.')

    def file_handle(self, excel_file):        
        name = ['msg']
        df = pd.read_excel(excel_file, header=None, names=name)
        df = pd.DataFrame(df).iterrows()
        data = []        
        for index, row in df:
            data.append({"msg": row['msg']})
        return data
        
    @ParsedClientView.init_parse 
    def get(self, req):        
        return BasicJsonResponse(data=self.model.objects.all())
    
    
class AddQ(AddMsg):
    model = Quote


class BlogerId(ParsedClientView): 

    @ParsedClientView.init_parse
    def get(self, req, size=None):                  
        return BasicJsonResponse(data=Bloger.objects.all())
    
    @ParsedClientView.init_parse
    @csrf_exempt
    @transaction.atomic
    def post(self, req):        
        if req.FILES:            
            blogers = file_handle(req.FILES['excelfile'])
            bulk_list = []
            for b in blogers:                   
                if not Bloger.objects.filter(nid=b['nid']):                    
                    bulk_list.append(Bloger(nid=b['nid'], blog_name=b['blog_name'], keyword=b['keyword']))
                else:
                    continue            
            try:
                Bloger.objects.bulk_create(bulk_list)          
            except DatabaseError as e:                
                return BasicJsonResponse(is_success=False, status=503, error_msg=e)
            return BasicJsonResponse(is_success=True, status=200)

        else:
            data = json.loads(req.body.decode('utf-8'))            
            if 'keyword' in data:                
                today = datetime.now().strftime('%Y%m%d')            
                keyword = data['keyword']            
                nums = [1, 31]
                blogs = []
                bulk_list = []
                for i in nums:            
                    blogs.extend(accumulator(keyword, i))        
                path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                create_dir(f"{path}\\form")
                file_name = f"blog_{keyword}_{today}.xlsx"
                wb = Workbook(f"{path}/form/{file_name}")
                ordered_list = ['nid', 'blog_name', 'keyword']
                ws = wb.add_worksheet()
                first_row = 0
                for header in ordered_list:
                    col = ordered_list.index(header)
                    ws.write(first_row, col, header)
                row = 1
                for b in blogs:
                    for k, v in b.items():
                        col = ordered_list.index(k)                                    
                        ws.write(row, col, v)
                    row += 1
                wb.close()                
                return BasicJsonResponse(data=file_name)
            
            else:
                nid = data['nid']
                try:
                    Bloger.objects.get(nid=nid)
                except Bloger.DoesNotExist:
                    b = Bloger(nid=nid)
                    b.save()
                    return BasicJsonResponse(is_success=True, status=200)
                return BasicJsonResponse(is_success=False, status=503, error_msg='해당 블로거가 이미 포함 되어 있습니다.')        

    def delete(self, req):
        data = json.loads(req.body.decode('utf-8'))
        if data.get('accs'):
            NaverAccounts.objects.filter(id__in=data['accs']).delete()
        if data.get('receivers'):
            BlogerId.objects.filter(id__in=data['receivers']).delete()
        if data.get('msg'):
            Message.objects.filter(id__in=data['msg']).delete()
        if data.get('quote'):
            Quote.objects.filter(id__in=data['quote']).delete()        
        return BasicJsonResponse(is_success=True, status=200)


class Login(ParsedClientView):        
    def get(self, req, **kwargs):        
        
        # if client:
        #     kwargs = {'cid': client.account}
        return render(req, "front.html", context=kwargs)

    def post(self, req):        
        res = HttpResponseRedirect(reverse('devoperator:login'))        
        account = req.POST['log_id']
        password = req.POST['log_pwd']                
        client = who_are_you(account)        
        if not client:
            res = self.get(req)  # 계정은 있는 계정인데 비번 틀린 경우
            return res
        hash_pwd = client.password        
        if check_password(password, hash_pwd):  # if same, returns True, or False            
            if client.auth:             
                login_cookie_value = generate_login_cookie(
                    account=account, user_agent=req.META['HTTP_USER_AGENT']
                )      
                reverse_page = reverse('devoperator:login')                
                res = HttpResponseRedirect(reverse_page)
                res.set_cookie('login', login_cookie_value, max_age=60 * 60 * 24 * 6, httponly=True)
                return res
        else:
            res = self.get(req)  # 계정은 있는 계정인데 비번 틀린 경우
        return res     
        
class Logout(View):
    @transaction.atomic
    def get(self, req):         
        # res = BaseJsonFormat()
        # res = HttpResponse(res, content_type="application/json")        
        res = HttpResponseRedirect(reverse('devoperator:login'))
        cookie_value = req.COOKIES.get('login', None)
        if cookie_value:
            login_session = LoginSession.objects.get(value=cookie_value)
            login_session.logged_out = True
            login_session.save()
            res.delete_cookie('login')
        return res
