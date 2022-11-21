from datetime import datetime
import random
import dramatiq
from typing import List, Tuple, Dict, Set
from decouple import config
from crawler.models import Bloger
from devoperator.models import Message, NaverAccounts, NoteSendingLog, Quote
from devoperator.tasks.blog_collect import Collector
from devoperator.tasks.login_request import NaverLogin
from devoperator.views.exception import *




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
    acc = NaverAccounts.objects.get(id=kwargs['account'][0])
    nid = acc.nid
    npw = acc.npw
    if not acc.validation:
        return False
    recs = [b for b in Bloger.objects.filter(id__in=kwargs['receivers'])]
    megs = [m.msg for m in Message.objects.filter(id__in=kwargs['message'])]
    quts = [q.qut for q in Quote.objects.filter(id__in=kwargs['quote'])]
    msg = f"{random.choice(megs)}\n\n{random.choice(quts)}"
    for r in recs:
        print(nid, npw, msg, r.bid)
    return True
                
                
        

