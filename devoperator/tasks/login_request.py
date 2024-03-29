import random
import re
import time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import rsa
import uuid
import lzstring

from devoperator.views.exception import LoginError



class NaverLogin:
    def __init__(self, uid, upw) -> None:
        self.headers = {
            'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "ko-KR,ko;q=0.9",
            "charset": "utf-8",
            "referer": "https://note.naver.com/",
            "Content-Type": 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        self._uid = uid
        self._upw = upw
        self.session = None
        self.key_url = 'https://nid.naver.com/login/ext/keys.nhn'
        self.login_url = 'https://nid.naver.com/nidlogin.login'
        self.encnm = None
        self.encpw = None        
    
    def _set_session(self):        
        retries = Retry(
            total=5,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.cookies.set(**{"domain": ".naver.com", 
                                    "rest": {"httpOnly": False, 
                                            "sameSite": None}, 
                                    "name": "NNB", 
                                    "path": "/", 
                                    "secure": True, 
                                    "value": "KSW3UMCJUFMGG"})
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def status_validation(self, url, session, post_data=None):
        if not session:
            raise RuntimeError
        wtime = range(2, 6)
        time.sleep(random.choice(wtime))
        if not post_data:
            res = session.get(url)            
        else:
            res = session.post(url, data=post_data)
        
        status = res.status_code
        if status == 200:            
            try:                
                return res.json()
            except:
                if "error" in res.text:
                    return None
                return res.text
        else:
            return None

    def _encrypt(self, key_str):
        def naver_style_join(l):
            return ''.join([chr(len(s)) + s for s in l])
        sessionkey, keyname, e_str, n_str = key_str.split(',')
        e, n = int(e_str, 16), int(n_str, 16)
        message = naver_style_join([sessionkey, self._uid, self._upw]).encode()        
        pubkey = rsa.PublicKey(e, n)
        encrypted = rsa.encrypt(message, pubkey)
        return keyname, encrypted.hex()    
    

    def _get_key_str(self):
        key_str = self.status_validation(self.key_url, self.session)
        self.encnm, self.encpw = self._encrypt(key_str)

    def login(self):
        self._set_session()
        self._get_key_str()
        bvsd_uuid = uuid.uuid4()
        encData = '{"a":"%s-4","b":"1.3.4","d":[{"i":"id","b":{"a":["0,%s"]},"d":"%s","e":false,"f":false},{"i":"%s","e":true,"f":false}],"h":"1f","i":{"a":"Mozilla/5.0"}}' % (bvsd_uuid, self._uid, self._uid, self._upw)
        bvsd = '{"uuid":"%s","encData":"%s"}' % (bvsd_uuid, lzstring.LZString.compressToEncodedURIComponent(encData))
        post_data = {
            'svctype': '0',
            'enctp': '1',
            'encnm': self.encnm,
            'enc_url': 'http0X0.0000000000001P-10220.0000000.000000www.naver.com',
            'url': 'www.naver.com',
            'smart_level': '1',
            'encpw': self.encpw,
            'bvsd': bvsd
        }
        res = self.status_validation(self.login_url, self.session, post_data=post_data)
        try:
            finalize_url = re.search(r'location\.replace\("([^"]+)"\)', res).group(1)
        except TypeError:
            raise LoginError
        if 'help' in finalize_url:
            raise LoginError
        res = self.status_validation(finalize_url, self.session)        
        return self.session