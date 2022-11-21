import functools
import json
from datetime import datetime
import random
import re
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy

import pandas as pd
from django.shortcuts import render
from django.views.generic import View, TemplateView
from django.views.generic.edit import CreateView, FormMixin, ProcessFormView
from openpyxl import load_workbook
from django.db import DatabaseError
from django.contrib import messages
from xlsxwriter import Workbook
from django.contrib import auth
from crawler.models import Bloger
from devoperator.models import Message, NaverAccounts, NoteSendingLog, Quote
from devoperator.tasks.distributor import task_distributor
from devoperator.views.exception import *
from naver.naver_login import NaverLogin, NoteSender
# from naver.bloger_collect import Collector
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from ..forms import *
from .common import BasicJsonResponse, HttpResponseBase
    

def merge_dicts(x, y):
    """
    Given two dicts, merge them into a new dict as a shallow copy.
    """
    z = x.copy()
    z.update(y)
    return z

class MultipleFormView(TemplateView):
    """
    View mixin that handles multiple forms / formsets.
    After the successful data is inserted ``self.process_forms`` is called.
    """
    form_classes = {}
    name_map = {'RecForm': Bloger, 'AccForm': NaverAccounts, 'QutForm': Quote}
    send_keys = ['accounts', 'receivers', 'message', 'quote']
    def get_context_data(self, **kwargs):
        context = super(MultipleFormView, self).get_context_data(**kwargs)
        forms_initialized = {name: form(prefix=name)
                             for name, form in self.form_classes.items()}

        return merge_dicts(context, forms_initialized)
    
    def file_flatten_save(self, name, files):
        def make_dict(keys, data):
            data_dict = {}
            for i, d in enumerate(data):
                data_dict[keys[i]] = d
            return data_dict
                
        load_wb = load_workbook(files[f"{name}-file"])        
        load_ws = load_wb['Sheet1']
        data_list = list()
        for n, row in enumerate(load_ws.rows):
            if name in ['AccForm', 'RecForm'] and n == 0:
                keys = [row[i].value for i in range(len(row))]
                continue
            elif name == 'QutForm':
                keys = ['qut']                
            data = [row[i].value for i in range(len(row))]
            data = make_dict(keys, data)            
            data_list.append(self.name_map[name](**data))
            
        try:
            self.name_map[name].objects.bulk_create(data_list, ignore_conflicts=True)
        except DatabaseError as e:
            return BasicJsonResponse(is_success=False, status=503, error_msg=e)
        else:
            return HttpResponseRedirect("/")

    def login_post(self):
        if self.request.method == 'POST':
            username = self.request.POST['uname']
            pwd = self.request.POST['pwd']
            user = auth.authenticate(username=username, password=pwd)
            if user:
                auth.login(self.request, user)
                messages.success(self.request, '로그인 성공')
            else:
                messages.error(self.request, '로그인 실패')
        
            
    def post(self, request):
        if request.user.is_authenticated:
            def get_form_name():
                for r in request.POST:
                    x = re.sub('\-.+', '', r)
                    if x in self.form_classes:
                        return x             
            def check():
                for k, v in request.POST.items():                
                    if k == 'csrfmiddlewaretoken':
                        continue                
                    if len(v) == 0:
                        return False
                    return True
            
            if request.FILES:            
                name = get_form_name()
                try:
                    self.file_flatten_save(name, request.FILES)
                except TypeError:
                    messages.warning(request, '입력한 데이터가 서로 다릅니다.')            
            if request.POST:            
                l1 = list(request.POST)
                contain = all(item in l1 for item in self.send_keys)
                if contain:
                    self.sending_method()
                else:
                    name = get_form_name()
                    try:
                        form_class = self.form_classes[name](request.POST)
                    except KeyError:
                        messages.warning(request, '데이터를 다시 선택해 주세요.')
                    else:                    
                        if form_class.is_valid():                
                            if check():                
                                form_class.save()
        else:
            self.login_post()
        return HttpResponseRedirect("/")
    
    def sending_method(self):
        acc = self.request.POST.getlist('accounts')
        recs = self.request.POST.getlist('receivers')
        msgs = self.request.POST.getlist('message')
        quts = self.request.POST.getlist('quote')
        task_distributor.send(**{"NoteSender":{"account":acc, "receivers":recs, "message":msgs, "quote":quts}})
        # acc = NaverAccounts.objects.get(id=acc[0])
        # nid = acc.nid
        # npw = acc.npw
        # msg = Message.objects.get(id=msgs[0]).msg
        # quotes = [q.qut for q in Quote.objects.filter(id__in=quts)]
        # receivers = [r.bid for r in Bloger.objects.filter(id__in=recs)]        
        
         # switchIp2()
        # nl = NaverLogin(nid, npw)    
        # session = nl.login()
        
        # for receiver in receivers:
        #     quote = random.choice(quotes)            
        #     m = f"{msg}\n\n{quote}"
        #     note = NoteSender(session=session, msg=m, taker=receiver)
        #     note.sending()
        
        


class NoteDataView(MultipleFormView):
    template_name = 'main.html'    
    model = NaverAccounts
    form_classes = {"AccForm": AccForm, "RecForm": RecForm, "MsgForm": MsgForm, "QutForm": QutForm}    
    
    
    def get_context_data(self, **kwargs):
        if self.request.user.is_authenticated:
            context = super().get_context_data(**kwargs)
            context['acc_list'] = self.model.objects.all()
            context['bloger_list'] = Bloger.objects.all()
            context['msg_list'] = Message.objects.all()
            context['quote_list'] = Quote.objects.all()
            context['log_list'] = NoteSendingLog.objects.all()
            for f in self.form_classes:            
                context[f] = self.form_classes[f]
        else:
            context = super().get_context_data(**kwargs)
        return context
                
 
@csrf_exempt
@login_required(login_url='')
def account_check(request):
    if request.method == 'POST':
        acc = json.loads(request.body.decode('utf-8'))['accounts']
        task_distributor.send(**{"NaverLogin": {"account":acc}})
        # acc = NaverAccounts.objects.get(id=acc[0])
        # nid = acc.nid
        # npw = acc.npw
        # nl = NaverLogin(nid, npw)
        # try:   
        #     nl.login()        
        # except LoginError:
        #     messages.warning(request, f'{nid} 계정을 확인 해주세요~!!')
        # else:
        #     acc.validation = True
        #     acc.save()
        return HttpResponseRedirect("/")


@login_required(login_url='')
def gather_taker(request):
    if request.method == 'POST':
        keyword = request.POST['keyword']
        task_distributor.send(**{"Collector": keyword})             
        return HttpResponseRedirect("/")

@csrf_exempt
@login_required(login_url='')
def sweep_data(request):    
    if request.method == 'DELETE':
        send_keys = ['accounts', 'receivers', 'message', 'quote']
        name_map = {'receivers': Bloger, 'accounts': NaverAccounts, 'quote': Quote, 'message': Message}
        data = json.loads(request.body.decode('utf-8'))        
        for k in send_keys:            
            if data[k]:
                model_instance = name_map[k].objects.filter(id__in=data[k])
                model_instance.delete()        
        messages.success(request, '삭제 완료')
        return HttpResponseBase('삭제 완료')            
    return HttpResponseRedirect("/")
                 

def logout(request):
    for n in NaverAccounts.objects.all():
        n.validation=False
        n.save()
    auth.logout(request)    
    return HttpResponseRedirect("/")