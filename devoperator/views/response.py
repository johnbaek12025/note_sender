import json
from django.views import View
from django.views.generic import FormView, ListView
from django.db import DatabaseError, transaction
from django.shortcuts import render
from datetime import datetime

from .common import HttpResponseBase, BasicJsonResponse
from xlsxwriter import Workbook
from crawler.models import Bloger
from devoperator.models import Message, NaverAccounts, NoteSendingLog, Quote
from devoperator.utility.utility import accumulator, file_handle
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from devoperator.utility.make_dir import create_dir
from ..forms import AccForm

class SendNote(View):
    pass


    
    
    

class AssignAccounts(FormView):
    template_name = 'main.html'
    form_class = AccForm
    success_url = '/'
    
    def form_valid(self, form):
        print(form)
        
class NoteDataList(View):
    template_name = 'main.html'    
    model = NaverAccounts
    
    def get_context_data(self, **kwargs):
        context = super(NoteDataList, self).get_context_data(**kwargs)
        context['acc_list'] = self.model.objects.all()
        context['bloger_list'] = Bloger.objects.all()
        context['msg_list'] = Message.objects.all()
        context['quote_list'] = Quote.objects.all()
        context['log_list'] = NoteSendingLog.objects.all()
        return context