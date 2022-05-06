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
            "Cookie": "NID_AUT=NID_AUT=oCdhxpIyQHj3Hv5z1ieZgWndTooNYxrPz2D+uXb1EJ6llEXSckC7I7GtSUHQ1cgV; NID_JKL=agg5XqVBfoKLzmyZYJIKVOt2FZYXEeRPcG/40u8rd9s=; NID_SES=AAABgwRHsKJB1RByeVTeg8LQBN/ddhWe/jxotDn6/qPJdqo8WxqsCtTHq3v5lPSo9oi6GkGnz1chw7rXJ9JAivNja9YpfpXsI7rPBVaqhnBiJBq/cdlWKROV/PPKz8ANHYsA3XfZK8HCOEJ8FRkFiQ1jl8/7tRRig4nF8ZwxfkaplhwaXcJ9gVfZHzFHeKpy7lY+OJuGJOV9ezmOZvx92h5S70fPkIJjmshXTX5bJ0XwKvZIPzW3pAmwu3EdC6uvsi73jEezZWdkTG1Njg2fYyFHFCtvVqoylWeATMuSfMoVQZCppYMc+FQUMRiJpH9Tak1EGNCVtBmx09Jf+yPUlTVYml9HUiKlQ7jqJ6/iomNzVw8cIXVxBAb2wtyWc6rgvSL4v32TP3AQfNXUOk1LsF8m0yQWgRBumMkBseTv7RWriDCF38a+9b48pmMFipbMOegKO2+BPIu+fsjN9A53lxoTBTW5CoU1iRXsTofIfiuiuhHoKmefVpmBK8jtoGuWkUdkKSUQmAxEklsjoutwCt/SSXI=; NNB=ISFWIGTVERTGE; nid_inf=1713101586; notecount=13",
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
print(info)
# token = info['token']
# svc = info['svcCode']
# data = data + f'&token={token}&svcCode={svc}'
# r = requests.post(url, headers = header, data=requote_uri(data), verify=True)
# print(r.content)
# print(vars(r.request))
