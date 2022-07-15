from celery import Task
from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime
from http import cookiejar
import json
import random
import re
from tabnanny import check
import time
import uuid
from django.dispatch import receiver
from devoperator.models import Ip, NaverAccounts, NoteSendingLog
from crawler.models import Bloger
import numpy
import requests
import rsa
import lzstring
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests.utils import requote_uri
from util.ip_util import get_myip, switchIp2



logger = get_task_logger(__name__)
def current_ip(tether=True):
    ip = get_myip()
    if tether:
        ip = switchIp2()
    try:
        get_ip = Ip.objects.get(address=ip)
    except Ip.DoesNotExist:
        Ip(address=ip).save()
        get_ip = Ip.objects.get(address=ip)
    return get_ip


@shared_task(name='login')
def run(**kwargs):
    wtime = numpy.arange(1, 3, 0.5)
    uid = kwargs.get('uid')
    upw = kwargs.get('upw')
    msg = kwargs.get('msg')
    receivers = kwargs.get('receivers')    
    acc_inst = NaverAccounts.objects.get(nid=uid)
    s = Session(uid, upw)
    check = s.check_account()    
    if isinstance(check, int):        
        for r in receivers:
            ip_inst = current_ip()
            time.sleep(random.choice(wtime))
            res = s.sending(msg, r)
            detail = json.loads(res.content.decode())            
            log_data = {
                "try_at": datetime.now().strftime('%Y-%m-%d, %H:%M:%S'),
                "try_at_date": datetime.now().strftime('%Y-%m-%d'),
                "receiver": Bloger.objects.get(nid=r),
                "msg": msg,
                "account": acc_inst,
                "ip": ip_inst,
            }            
            if 'Result' in detail:
                log_data['error_msg'] = detail['Message']
            elif 'status' in detail:
                log_data['error_msg'] = detail['Message']
            else:                        
                log_data['is_success'] = True
            try:
                print(log_data)
                log = NoteSendingLog(**log_data)
                log.save()
            except:
                print('error')
                continue
        
    else:
        log_data = {
                        "account": acc_inst,
                        "try_at": datetime.now().strftime('%Y-%m-%d, %H:%M:%S'),
                        "try_at_date": datetime.now().strftime('%Y-%m-%d'),
                        'receiver': random.choice(receivers),
                        'msg': msg,
                        'error_msg': check,
                    }
    

class NaverLogin:
    def __init__(self, uid, upw) -> None:
        self.request_headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "ko-KR,ko;q=0.9",
            "charset": "utf-8",
            "referer": "https://note.naver.com/",
        }
        self._uid = uid
        self._upw = upw

    def encrypt(self, key_str):
        def naver_style_join(l):
            return ''.join([chr(len(s)) + s for s in l])

        sessionkey, keyname, e_str, n_str = key_str.split(',')    
        e, n = int(e_str, 16), int(n_str, 16)
        message = naver_style_join([sessionkey, self._uid, self._upw]).encode()        
        pubkey = rsa.PublicKey(e, n)    
        encrypted = rsa.encrypt(message, pubkey) 
        return keyname, encrypted.hex()
    
    def naver_session(self):
        key_str = requests.get('https://nid.naver.com/login/ext/keys.nhn').content.decode("utf-8")
        encnm, encpw = self.encrypt(key_str)        
        s = requests.Session()
        s.headers.update(self.request_headers)

        s.cookies.set(**{"domain": ".naver.com", "rest": {"httpOnly": False, "sameSite": "no_strict"}, "name": "NNB", "path": "/", "secure": True, "value": "ISFWIGTVERTGE"})
        #s.cookies.set(**{"domain": "note.naver.com", "rest": {"httpOnly": False}, "name": "notecount", "path": "/", "secure": False, "value": "13"})
        retries = Retry(
            total=5,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )
        s.mount('https://', HTTPAdapter(max_retries=retries))
        bvsd_uuid = uuid.uuid4()
        encData = '{"a":"%s-4","b":"1.3.4","d":[{"i":"id","b":{"a":["0,%s"]},"d":"%s","e":false,"f":false},{"i":"%s","e":true,"f":false}],"h":"1f","i":{"a":"Mozilla/5.0"}}' % (bvsd_uuid, self._uid, self._uid, self._upw)
        bvsd = '{"uuid":"%s","encData":"%s"}' % (bvsd_uuid, lzstring.LZString.compressToEncodedURIComponent(encData))
        resp = s.post('https://nid.naver.com/nidlogin.login', data={
            'svctype': '0',
            'enctp': '1',
            'encnm': encnm,
            'enc_url': 'http0X0.0000000000001P-10220.0000000.000000www.naver.com',
            'url': 'www.naver.com',
            'smart_level': '1',
            'encpw': encpw,
            'bvsd': bvsd
        }, headers=self.request_headers)
        try:
            finalize_url = re.search(r'location\.replace\("([^"]+)"\)', resp.content.decode("utf-8")).group(1)
        except:
            if "안전한 로그인을 위해 주소창의 URL과 자물쇠 마크를 확인하세요!" in resp.content.decode("utf-8"):
                return '아이디 및 비밀번호 또는 캡차를 확인 해주세요'
        # print('f-url:', finalize_url)
        s.get(finalize_url)
        res = s.get("https://m.naver.com/aside/")
        if self._uid in res.text:
            print('로그인 성공')
        return s
        

class Session(NaverLogin):
    def __init__(self, uid, upw) -> None:        
        super().__init__(uid, upw)        
        self.urls = "https://note.naver.com/json/write/"
        self.url = "https://note.naver.com/json/write/send/"        

    def check_account(self):
        try:
            with self.naver_session() as session:
                get_token = session.post(self.urls)
        except:
            return '아이디 및 비밀번호 또는 캡차를 확인 해주세요'
        token = json.loads(get_token.content.decode('utf-8'))        
        if 'todaySentCount' in token:
            return 50-int(token.get('todaySentCount'))
        else:
            return token.get('LoginStatus')

    def sending(self, msg, taker):
        data = {
            "svcType": "undefined",
            "svcId": None,
            "svcName": None,
            'content': msg,
            "isReplyNote": 0,
            "targetUserId": taker,
            "isBackup": 1,
            "u": self._uid,
        }
        with self.naver_session() as session:
            get_token = session.post(self.urls, json=data)
        token = json.loads(get_token.content.decode())        
        if "token" not in token:
            return False
        data.update({"token": token['token'], "svcCode": token['svcCode']})
        #res = self.session.get(f"https://note.naver.com/json/captcha/create/?targetUserId={taker}&u={self._uid}", headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
        #print('captcha:', vars(res))     
        with self.naver_session() as session:
            res = session.post(self.url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
        return res



    