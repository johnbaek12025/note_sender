import json
import os
from django.dispatch import receiver
from django.shortcuts import render
from django.views import View
from django.shortcuts import render
from datetime import datetime
from django.http import HttpResponse
from django.db import DatabaseError, transaction


from crawler.models import Bloger
from devoperator.models import Ip, NoteSendingLog
from devoperator.utility.make_dir import create_dir
from devoperator.views.common import BasicJsonResponse

from django.views.decorators.csrf import csrf_exempt
import traceback




class SendCrawler(View):
    def get(self, req):
        logs = NoteSendingLog.objects.select_related('account').select_related('receiver').filter(is_success=False)
        data = []
        for l in logs:
            data.append({'acc_id': l.account.nid,
                        'acc_pw': l.account.npw,
                        'msg': l.msg,
                        'r_id': l.receiver.nid})
        return BasicJsonResponse(data=data)

    @csrf_exempt
    @transaction.atomic
    def post(self, req):        
        data = json.loads(req.body.decode('utf-8'))                
        try:
            self.preprocess(data)
        except Exception:
            print(traceback.print_exc())
            return BasicJsonResponse(msg='error 발생', status=403)
        return BasicJsonResponse(is_success=True, status=200)
            
    def preprocess(self, data):
        def current_ip(ip):            
            if not ip:
                return False
            try:                
                get_ip = Ip.objects.get(address=ip)
            except Ip.DoesNotExist:
                ip_ad = Ip(address=ip)
                ip_ad.save()
                get_ip = Ip.objects.get(address=ip)
            return get_ip
        ip_obj = current_ip(data['ip'])
        receiver = data['receiver']        
        r_inst = Bloger.objects.get(nid=receiver)        
        log = NoteSendingLog.objects.get(receiver=r_inst.id, try_at__isnull=True)
        if 'error_msg' in data:
            log.error_msg = data['error_msg']
        else:
            log.is_success = data['is_success']
        log.ip = ip_obj
        log.try_at_date = data['try_at_date']
        log.try_at = data['try_at']
        log.msg = data['msg']
        log.save()
        return True