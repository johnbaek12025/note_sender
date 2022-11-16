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

from crawler.models import Bloger
from devoperator.models import Message, NaverAccounts, NoteSendingLog, Quote
from devoperator.utility.make_dir import create_dir
from devoperator.utility.utility import accumulator, file_handle
from naver.exceptions import LoginError
from naver.naver_login import NaverLogin, NoteSender
# from naver.bloger_collect import Collector

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
            
    def post(self, request):        
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
        return HttpResponseRedirect("/")
    
    def sending_method(self):
        acc = self.request.POST.getlist('accounts')
        recs = self.request.POST.getlist('receivers')
        msgs = self.request.POST.getlist('message')
        quts = self.request.POST.getlist('quote')
        
        if len(acc) > 1:
            messages.warning(self.request, '발신 계정은 한 개만 선택 해주세요~~!!')
        if len(msgs) > 1:
            messages.warning(self.request, '메세지는 한 개만 선택 해주세요~~!!')
        acc = NaverAccounts.objects.get(id=acc[0])
        nid = acc.nid
        npw = acc.npw
        msg = Message.objects.get(id=msgs[0]).msg
        quotes = [q.qut for q in Quote.objects.filter(id__in=quts)]
        receivers = [r.bid for r in Bloger.objects.filter(id__in=recs)]        
         # switchIp2()
        nl = NaverLogin(nid, npw)    
        session = nl.login()
        
        for receiver in receivers:
            quote = random.choice(quotes)            
            m = f"{msg}\n\n{quote}"
            note = NoteSender(session=session, msg=m, taker=receiver)
            note.sending()
        
        


class NoteDataView(MultipleFormView):
    template_name = 'main.html'    
    model = NaverAccounts
    form_classes = {"AccForm": AccForm, "RecForm": RecForm, "MsgForm": MsgForm, "QutForm": QutForm}    
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['acc_list'] = self.model.objects.all()
        context['bloger_list'] = Bloger.objects.all()
        context['msg_list'] = Message.objects.all()
        context['quote_list'] = Quote.objects.all()
        context['log_list'] = NoteSendingLog.objects.all()
        for f in self.form_classes:            
            context[f] = self.form_classes[f]
        return context
 

def account_check(request):
    acc = request.POST['accounts']
    acc = NaverAccounts.objects.get(id=acc[0])
    nid = acc.nid
    npw = acc.npw
    nl = NaverLogin(nid, npw)
    try:   
        session = nl.login()
    except LoginError:
        messages.warning(request, f'{nid} 계정을 확인 해주세요~!!')
    else:
        acc.validation = True
        acc.save()
    return HttpResponseRedirect("/")

def sweep_taker(request):
    keyword = request.POST['keyword']
    # c = Collector(keyword)
    # c.main()
    return HttpResponseRedirect("/")