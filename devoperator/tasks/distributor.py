from datetime import datetime
import random
import dramatiq
from typing import List, Tuple, Dict, Set
from decouple import config
from crawler.models import Bloger
from devoperator.models import Message, NaverAccounts, NoteSendingLog, Quote
from devoperator.tasks.blog_collect import Collector
from devoperator.tasks.login_request import NaverLogin
from devoperator.tasks.note_sending import NoteSender
from devoperator.tasks.exception import *
from django.contrib import messages



@dramatiq.actor
def task_distributor(**kwargs):    
    for k, v in kwargs.items():        
        if isinstance(v, str):
            c = Collector(v)
            c.main()
            return
        else:
            if len(v) > 1:
                sending_process(**v)
                
            else:
                data = v['account']
                acc = NaverAccounts.objects.get(id=data[0])
                if acc.validation:
                    return
                else:
                    print(acc.nid)
                    nl = NaverLogin(acc.nid, acc.npw)
                    s = nl.login()
                    if s:
                        acc.validation = True
                        acc.save()
                    return
                        


def sending_process(**kwargs):    
    try_at_date = datetime.now().strftime('%Y%m%d')
    acc = NaverAccounts.objects.get(id=kwargs['account'][0])
    nid = acc.nid
    npw = acc.npw
    if not acc.validation:
        return False
    recs = [b for b in Bloger.objects.filter(id__in=kwargs['receivers'])]
    megs = [m.msg for m in Message.objects.filter(id__in=kwargs['message'])]
    quts = [q.qut for q in Quote.objects.filter(id__in=kwargs['quote'])]
    msg = f"{random.choice(megs)}\n\n{random.choice(quts)}"
    nl = NaverLogin(nid, npw)
    session = nl.login()    
    if nl:
        bulk_data = []
        """
        {'Message': '쪽지를 성공적으로 보냈습니다.\n\n내게쓴쪽지는 [내게쓴쪽지함]에서 확인할 수 있습니다.', 
        'failUserList': '', 
        'todaySentCount': 0, 
        'status': 'success', 
        'Result': 'OK'}
        """
        for r in recs:            
            try_at = datetime.now().strftime('%Y%m%d %H%M%S')
            s = NoteSender(session=session, msg=msg, taker=r.bid)            
            result = s.sending()
            print(result)
            if result['status'] == 'success':
                l = NoteSendingLog(account=acc, receiver=r, is_success=True, try_at=try_at, try_at_date=try_at_date)
                l.save()
            else:                
                l = NoteSendingLog(account=acc, receiver=r, error_msg=result['Message'], try_at=try_at, try_at_date=try_at_date)
                l.save()        
    return True
                
                
        

