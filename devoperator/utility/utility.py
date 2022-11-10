import random
import string
from xlsxwriter import Workbook
from pathlib import Path
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup as bf

from devoperator.views.exception import IntegrityError


def file_handle(excel_file):        
        df = pd.read_excel(excel_file)
        df = pd.DataFrame(df).iterrows()
        data = []
        duple = []
        for index, row in df:
            if row['nid'] not in duple:
                duple.append(row['nid'])
                data.append({'nid': row['nid'], 'blog_name': row['blog_name'], 'keyword': row['keyword']})        
            else:
                continue                
        return data             

def accumulator(keyword, page):        
    url = f"https://s.search.naver.com/p/blog/search.naver?where=blog&sm=tab_pge&api_type=1&query={keyword}&rev=44&start={page}&dup_remove=1&post_blogurl=&post_blogurl_without=&nso=&dkey=0&source_query=&nx_search_query={keyword}&spq=0&_callback=viewMoreContents"
    # url = requote_uri(url)
    res = requests.get(url)
    info = bf(res.text, 'html.parser')
    data = []
    for a in info.find_all('a', {"class": '\\"sub_txt'}):    
        res1 = re.sub(r'[a-z./:"\\]+.com/','', a['href'])
        nid = re.sub(r'\\"','', res1)
        b_name = a.text
        data.append({'nid': nid, 'blog_name': b_name, 'keyword': keyword})
    return data