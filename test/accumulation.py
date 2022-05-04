import json
import os
import sys
import requests
from requests.utils import requote_uri
from bs4 import BeautifulSoup as bf
import re

keyword = '강아지 장난감'
url = f"https://s.search.naver.com/p/blog/search.naver?where=blog&sm=tab_pge&api_type=1&query={keyword}&rev=44&start=1&dup_remove=1&post_blogurl=&post_blogurl_without=&nso=&dkey=0&source_query=&nx_search_query={keyword}&spq=0&_callback=viewMoreContents"
# url = requote_uri(url)
res = requests.get(url)    
info = bf(res.text, 'html.parser')
for a in info.find_all('a', {"class": '\\"sub_txt'}):    
    res1 = re.sub(r'[a-z./:"\\]+.com/','', a['href'])
    id = re.sub(r'\\"','', res1)
    print(a.text)
    print(id)


url = f"https://s.search.naver.com/p/blog/search.naver?where=blog&sm=tab_pge&api_type=1&query={keyword}&rev=44&start=31&dup_remove=1&post_blogurl=&post_blogurl_without=&nso=&dkey=0&source_query=&nx_search_query={keyword}&spq=0&_callback=viewMoreContents"
# url = requote_uri(url)
res = requests.get(url)    
info = bf(res.text, 'html.parser')
a_tag = info.find_all('a', {"class": '\\"sub_thumb\\"'})
for a in a_tag:    
    res1 = re.sub(r'[a-z./:"\\]+.com/','', a['href'])    
    id = re.sub(r'\\"','', res1)    
    ids.add(id)
print(ids)
