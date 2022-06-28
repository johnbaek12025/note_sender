import json
import os
from django.shortcuts import render
from django.views import View
from django.shortcuts import render
from datetime import datetime
from django.http import HttpResponse
from django.db import DatabaseError, transaction
from bs4 import BeautifulSoup as bf
import requests
import re
from crawler.models import Bloger
from devoperator.models import NoteSendingLog
from devoperator.views import BasicJsonResponse
from xlsxwriter import Workbook
from pathlib import Path
import pandas as pd


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


class BlogerId(View):
    def get(self, req, size=None):            
        
            return BasicJsonResponse(data=Bloger.objects.filter())

    @transaction.atomic
    def post(self, req):
        if req.FILES:            
            blogers = file_handle(req.FILES['excelfile'])
            bulk_list = []
            for b in blogers:                   
                if not Bloger.objects.filter(nid=b['nid']):                    
                    bulk_list.append(Bloger(nid=b['nid'], blog_name=b['blog_name'], keyword=b['keyword']))
                else:
                    continue            
            try:
                Bloger.objects.bulk_create(bulk_list)          
            except DatabaseError as e:                
                return BasicJsonResponse(is_success=False, status=503, error_msg=e)
            return BasicJsonResponse(is_success=True, status=200)

        else:
            data = json.loads(req.body.decode('utf-8'))     
            if 'keyword' in data:            
                downloads_path = str(Path.home() / "Downloads")            
                today = datetime.now().strftime('%Y%m%d')            
                keyword = data['keyword']            
                nums = [1, 31]
                blogs = []
                bulk_list = []
                for i in nums:            
                    blogs.extend(accumulator(keyword, i))            
                wb = Workbook(f"{downloads_path}/blog_{keyword}_{today}.xlsx")
                ordered_list = ['nid', 'blog_name', 'keyword']
                ws = wb.add_worksheet()
                first_row = 0
                for header in ordered_list:
                    col = ordered_list.index(header)
                    ws.write(first_row, col, header)
                row = 1
                for b in blogs:
                    for k, v in b.items():
                        col = ordered_list.index(k)                                    
                        ws.write(row, col, v)
                    row += 1
                wb.close()                
                return BasicJsonResponse(is_success=True, status=200)
            
            else:
                nid = data['nid']
                try:
                    Bloger.objects.get(nid=nid)
                except Bloger.DoesNotExist:
                    b = Bloger(nid=nid)
                    b.save()
                    return BasicJsonResponse(is_success=True, status=200)
                return BasicJsonResponse(is_success=False, status=503, error_msg='해당 블로거가 이미 포함 되어 있습니다.')        

    def delete(self, req):
        data = json.loads(req.body.decode('utf-8'))
        bloger = BlogerId.objects.get(id__in=data['id'])
        bloger.delete()
        return BasicJsonResponse(is_success=True, status=200)
        

class SendCrawler(View):
    def get(self, req):
        logs = NoteSendingLog.objects.select_related('account').select_related('receiver').filter(is_success=False)
        data = []
        for l in logs:
            data.append({'acc_id': l.account.nid,
                        'acc_pw': l.account.npw,
                        'r_id': l.receiver.nid})
        return BasicJsonResponse(data=data)

    def post(self, req):
        pass