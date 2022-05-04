import json
import random
from urllib.request import proxy_bypass
import requests
from requests.utils import requote_uri

header =  {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Connection": "keep-alive", 
            "Cookie": "NID_AUT=ZtToe1vYrY48xMA7yLN5pvjRoiwKn3Zwzj/GpOOy4Iu5+xQg6HIVpHg4cEszuaaV; NID_JKL=AWahEzJeAp2Xq1m2O8+xyULx/u4M/dXSID5wxdpJhOY=; NID_SES=AAABiIkmCXChWHePjGFgdsH8iStL/VJ9RuXN/7xMtKbftgTKhgHlJgDYoFDR5y41r6TxomLXdpbsbJJk1fr6NdBcyG5SkgxdsIcmPta2ADp1CP8JcPN1LBlHBqapM+SLQ07/dxJB1Osa2jHg/LxrBu50TfHFhWxxysDtFhj7b03vBP2p17jeoQwz9TPQ9u1YQ2CPeJ2uJXHmDGqDENcuNDU66CaozwfVde8NushXAN0kZRYWvLaGH7YFrxbqvPJV4S9s5VyzkUAFlMsKSQ95gXFqiEu1cE0PK5e0SRdhBuidM+rAM8NbT9z14i9lnSSHZPk3j3InkDYne12vcNIa1e9RFlxTIMYbBQWoBQFcv+yLg4FG5QPbzsGMK5pOQvbNHo+98swZMX/F9/pxS9LByv50ut97llJWItc6MGHs3yA6Ye3V7MW0qKPKa3ALKMHBRH2lcq/GdxjkyHBfNAocAr+009YpGKLm1WVKna1RjdVk/Xrg0TObjDqiRdtBtlcElLRoR5KUA6FOz7SUzatgmOP9qJw=; NNB=ISFWIGTVERTGE; nid_inf=460410445; notecount=13",
            "Content-Type": "application/x-www-form-urlencoded",
            "origin": "https://note.naver.com",
            "sec-ch-ua-platform": "Windows",
            "charset": "utf-8"
            }
msg = '안녕하세요 테스트 입니다.'

data = 'svcType=undefined&content=Asdasfasdfsd&isReplyNote=0&targetUserId=blackpeacock374&isBackup=1&u=blackpeacock374'
url = 'https://note.naver.com/json/write/send/'
urls = 'https://note.naver.com/json/write/'
get_info = requests.post(urls, headers = header, data=requote_uri(data), verify=True)
info = json.loads(get_info.content.decode())
token = info['token']
svc = info['svcCode']
data = data + f'&token={token}&svcCode={svc}'
r = requests.post(url, headers = header, data=requote_uri(data), verify=True)
print(r.content)
print(vars(r.request))
