import requests
import re
from devoperator.utility.utility import make_excel
from bs4 import BeautifulSoup as bf
import time
import random


class Collector:
    def __init__(self, keyword) -> None:
        self.url = "https://s.search.naver.com/p/blog/search.naver?where=blog&sm=tab_pge&api_type=1&query={keyword}&rev=44&start={cnt}&dup_remove=1&post_blogurl=&post_blogurl_without=&nso=&dkey=0&source_query=&nx_search_query={keyword}&spq=0&_callback=viewMoreContents"
        self.keyword = keyword
        self.columns = ['bid', 'blog_name', 'keyword']
    
    def set_session(self):
        return requests.Session()

    
    def main(self):
        s = self.set_session()
        data = {}
        for i in range(31):
            cnt = i * 30 + 1
            print(cnt)
            url = self.url.format(keyword=self.keyword, cnt=cnt)
            res = self.status_validation(url, s)
            d =  self.collect_bloger(res)
            data.update(d)
        data = self.dict_reset(data)
        print('data')
        make_excel(self.columns, data, self.keyword)
        
    
    def dict_reset(self, data):
        list_dict = []
        for k, v in data.items():
            list_dict.append({'bid':k, 'blog_name': v[0], 'keyword': v[1]})
        return list_dict
    
    def collect_bloger(self, res):
        info = bf(res, 'html.parser')
        data = {}
        for a in info.find_all('a', {"class": '\\"sub_txt'}):
            res1 = re.sub(r'[a-z./:"\\]+.com/','', a['href'])            
            nid = re.sub(r'\\"','', res1)
            b_name = a.text
            if not nid:
                continue
            data[nid] = [b_name, self.keyword]
        return data    
    
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
                return res.text
        else:
            return None
