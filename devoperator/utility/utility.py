import random
import string
from xlsxwriter import Workbook
from pathlib import Path
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup as bf

from devoperator.models import Account, LoginSession
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

def who_are_you(account):
    who = None

    try:
        who = Account.objects.get(account=account)
    except Account.DoesNotExist:
        pass    
    return who


def generate_login_cookie(account, user_agent, session_cls=LoginSession):
    while True:
        try:
            login_cookie_value = ''.join(
                random.choices(string.ascii_letters + string.digits, k=random.randint(60, 70)))
        except AttributeError:

            def random_choices(p, k):  # random.choices -> 3.6 up, so this func is for 3.5 down
                temp = []
                for _ in range(k):
                    temp.append(p[random.randrange(len(p))])
                return temp

            login_cookie_value = ''.join(
                random_choices(string.ascii_letters + string.digits, k=random.randint(60, 70)))
            
        try:
            session_cls(
                account=account,
                value=login_cookie_value,
                user_agent=user_agent,
                logged_out=False,                
            ).save()
        except IntegrityError('sesseion value overlaps, retry to create and save'):
            continue
        else:
            break

    return login_cookie_value