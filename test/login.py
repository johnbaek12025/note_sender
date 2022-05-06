from http import cookiejar
import json
import re
import uuid
import requests
import rsa
import lzstring
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests.utils import requote_uri

class NaverLogin:
    def __init__(self, uid, upw) -> None:
        self.request_headers = {
            'User-agent': 'Mozilla/5.0',
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "ko-KR,ko;q=0.9",
            "Pragma": "no-cache",
            "charset": "utf-8",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "referer": "https://note.naver.com/",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
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
        
        s.cookies.set(**{"domain": ".naver.com", "rest": {"httpOnly": False, "sameSite": "no_strict"}, "name": "NNB", "path": "/", "secure": True, "value": "ISFWIGTVERTGE"})
        s.cookies.set(**{"domain": "note.naver.com", "rest": {"hostOnly": True}, "name": "notecount", "path": "/", "secure": False, "value": "13"})
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
            print(resp.content.decode("utf-8"))        
        s.get(finalize_url)
        return s    
        

class SendMessage(NaverLogin):
    def __init__(self, uid, upw) -> None:        
        super().__init__(uid, upw)
        self.session = self.naver_session()
        self.urls = "https://note.naver.com/json/write/"
        self.url = "https://m.note.naver.com/mobile/mobileCaptchaViewCheck.nhn?"

    def sending(self, msg, taker):        
        data = {
            "svcType": "undefined",
            "svcId": '',
            "svcName": '',
            'content': msg,
            "isReplyNote": 0,
            "targetUserId": taker,
            "isBackup": 1,
            "u": self._uid,
        }
        get_token = self.session.post(self.urls, data=data)
        print(get_token.cookies)
        token = json.loads(get_token.content.decode())
        data.update({"token": token['token'], "svcCode": token['svcCode']})
        res = self.session.post(self.url, data=data)        
        return res

if __name__ == "__main__":
    msg = 'Asdasfasdfsd'    
    message = SendMessage('lazyfrog495', 'w12z9y9aycmu')    
    res = message.sending(msg, 'blackpeacock374')
    print(vars(res.request))
    print('\n')
    print(vars(res))

    