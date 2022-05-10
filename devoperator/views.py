import json
from pathlib import Path
import random
from sre_constants import SUCCESS
import time
from datetime import datetime
import unicodedata
from django.dispatch import receiver
from django.views import View
from django.db import DatabaseError, transaction
from django.db.models import QuerySet, Model
from django.forms import model_to_dict
from django.http import HttpResponse
from django.shortcuts import render
from datetime import datetime

from xlsxwriter import Workbook
from crawler.models import Bloger
from devoperator.models import Ip, Message, NaverAccounts, NoteSendingLog, Quote, Transition
from http import cookiejar
import json
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests.utils import requote_uri
from util.ip_util import switchIp2, get_myip
from util.naver_note import Session
from django.views.decorators.csrf import csrf_exempt
import pandas as pd


def check_account(req):
    if req.method == 'POST':
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
        


def download_account_excel(req):
    if req.method == 'GET':
        downloads_path = str(Path.home() / "Downloads")            
        today = datetime.now().strftime('%Y%m%d')
        wb = Workbook(f"{downloads_path}/네이버_계정_형식_{today}.xlsx")
        ordered_list = ['아이디', '비밀번호']
        ws = wb.add_worksheet()
        first_row = 0
        for header in ordered_list:
            col = ordered_list.index(header)
            ws.write(first_row, col, header)        
        wb.close()                
        return BasicJsonResponse(is_success=True, status=200)
    

def main_page(req):
    if req.method == 'GET':
        data = {}
        todate = datetime.now().strftime('%Y-%m-%d')
        data['receiver'] = [(b.id, b.nid, b.keyword, b.blog_name) for b in Bloger.objects.all()]
        data['account'] = [(a.id, a.nid, a.npw)for a in NaverAccounts.objects.all()]
        data['message'] = [(m.id, m.msg)for m in Message.objects.all()]        
        data['quote'] = [(q.id, q.msg)for q in Quote.objects.all()]
        data['log'] = ((l.id, l.account.nid, "성공" if l.is_success else l.error_msg, l.receivers.nid, l.ip.address,)for l in NoteSendingLog.objects.select_related('account').select_related('receivers').select_related('ip').filter(try_at_date=todate))
        return render(req, "front.html", context=data)
    elif req.method == 'DELETE':
        data = json.loads(req.body.decode('utf-8'))
        accs = data['accs']
        receivers = data['receivers']        
        msg = data['msg']
        quote = data['quote']
        if accs:
            acc = NaverAccounts.objects.filter(id__in=accs)
            acc.delete()
        if receivers:
            rec = Bloger.objects.filter(id__in=receivers)
            rec.delete()
        if msg:
            msg = [int(i)for i in data['msg']]
            m = Message.objects.filter(id__in=msg)            
            m.delete()
        if quote:
            quote = [int(i)for i in data['quote']]
            q = Quote.objects.filter(id__in=quote)            
            q.delete()
        return BasicJsonResponse(is_success=True, status=200)


class SendNote(View):
    @transaction.atomic
    @csrf_exempt
    def post(self, req):
        def current_ip(tether=True) -> QuerySet:            
            if tether:
                ip = switchIp2()
            try:
                get_ip = Ip.objects.get(address=ip)
            except Ip.DoesNotExist:
                Ip(address=ip).save()
                get_ip = Ip.objects.get(address=ip)
            return get_ip

        def list_chunk(lst, n):
            li = []
            for i in range(0, len(lst), n):
                if i == len(lst) - n - 1:
                    li.append(lst[i:])
                    break
                else:
                    li.append(lst[i:i+n])
            return li

        data = json.loads(req.body.decode('utf-8'))
        acc_ids = data.get('accs') # 발신 계정들
        msg_ids = data.get('msg') # 메시지        
        receiver_ids = data.get('receivers') # 수신자        
        quote_ids = data.get('quote', '') # 명언 포함 여부               
        tether_bul = data.get('tether', True) # 테더링유무                
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
        wtime = [i for i in range(2, 7)]        
        bulk_list = []
        for acc in NaverAccounts.objects.filter(id__in=acc_ids):            
            session = Session(acc.nid, acc.npw)
            ip_object = current_ip(tether_bul)
            time.sleep(random.choice(wtime))
            limit_cnt = session.check_account()
            if not limit_cnt:
                return BasicJsonResponse(is_success=False, status=503, error_msg='해당 계정은 오늘 50개의 쪽지를 다 보냈습니다.')
            today = datetime.now().strftime('%Y-%m-%d')
            msg = random.choice(msgs)            
            for r in Bloger.objects.filter(id__in=receiver_ids):
                result = session.sending(msg, r.nid)
                time.sleep(random.choice(wtime))
                res = json.loads(result.content.decode())                
                if 'failUserList' in res:
                    bulk_list.append(NoteSendingLog(
                                account=acc,
                                receivers=r,
                                ip=ip_object,
                                error_msg = res['Message'],
                                try_at_date=today,
                                msg=f"{r.nid} 전송 실패"))                    
                elif 'Result' in res:
                    bulk_list.append(NoteSendingLog(
                                account=acc,
                                receivers=r,
                                ip=ip_object,
                                error_msg = res['LoginStatus'],
                                try_at_date=today,
                                msg=f"{r.nid} 전송 실패"
                    ))
                else:
                    bulk_list.append(NoteSendingLog(
                                account=acc,
                                receivers=r,
                                ip=ip_object,
                                is_success=True,
                                try_at_date=today,
                                msg=res['Message']
                    ))                    
        try:
            NoteSendingLog.objects.bulk_create(bulk_list)
        except DatabaseError as e:                
                return BasicJsonResponse(is_success=False, status=503, error_msg=e)

        return BasicJsonResponse(is_success=True, status=200)

    
    def get(self, req):        
        todate = datetime.now().strftime('%Y-%m-%d')
        log = NoteSendingLog.objects.select_related('account').select_related('ip').select_related('receivers').filter(try_at_date=todate)        
        for l in log:
            yield{
                "account": l.account.nid,
                "msg":l.msg,
                "ip": l.ip.address,
                "receiver": l.receiver.nid,
                "blog_name": l.receiver.blog_name,
                "keyword": l.receiver.keyword,
                "result": l.is_success if l.is_success else l.error_msg,
                "try_date": l.try_at_date,
                "try_at": l.try_at,
            }
        
    

class AssignAccounts(View):
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

    def put(self, req, id):
        data = json.loads(req.body.decode('utf-8'))        
        account = NaverAccounts.objects.get(id=id)        
        account.modified_at = datetime.now()
        account.npw = data['npw']
        account.save()
        return BasicJsonResponse(is_success=True, status=200)

    def get(self, req):        
        return BasicJsonResponse(data=NaverAccounts.objects.filter())

    def delete(self, req):
        data = json.loads(req.body.decode('utf-8'))
        acc_ids = data.get('acc_id')        
        accs = NaverAccounts.objects.filter(id__in=acc_ids)
        accs.delete()
        return BasicJsonResponse(is_success=True, status=200)


class AddMsg(View):
    model = Message

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
                l = self.model.objects.filter(msg__in=msg)
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
        
    def put(self, req):
        data = json.loads(req.body.decode('utf-8'))

    def get(self, req):
        return BasicJsonResponse(data=self.model.objects.filter())


class AddTrs(AddMsg):
    model = Transition
    
    
class AddQ(AddMsg):
    model = Quote




class HttpResponseBase(HttpResponse):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._headers = self.headers 


class BasicJsonResponse(HttpResponseBase):

    def __init__(self, *, is_success: bool = True, status: int = 200, data=None, msg=None, error_msg=None, **kwargs):

        json_content = dict()
        json_content['is_success'] = is_success
        '''""{"date": , "content": }""'''

        if msg is not None:
            json_content['msg'] = msg
        if error_msg is not None:
            json_content['error_msg'] = error_msg

        if status is None:
            if is_success:
                status = 200
            else:
                raise Exception("status 값을 입력해야합니다.")   # todo: custom exception class

        if data is not None:
            if type(data) is QuerySet:
                json_content['data'] = list(data.values())
            elif isinstance(data, Model):
                json_content['data'] = model_to_dict(data)
            else:
                json_content['data'] = data

        super().__init__(json.dumps(json_content, default=str, ensure_ascii=False), content_type="application/json; charset=utf-8", status=status, **kwargs)
