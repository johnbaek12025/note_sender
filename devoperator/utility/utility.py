import random
import string
from xlsxwriter import Workbook
from pathlib import Path
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup as bf

from devoperator.views.exception import IntegrityError       
import json
import os
from xlsxwriter import Workbook

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')


def get_bring_data(file_name):
    if file_name == 'debug':
        fp = os.path.join(CONFIG_DIR, file_name)
        if not os.path.exists(fp):
            return False
    fp = os.path.join(CONFIG_DIR, file_name)
    with open(fp, 'r') as f:
        return json.load(f)

def make_excel(columns:list, data:list, file_name):
    wb = Workbook(f"{file_name}.xlsx")
    ws = wb.add_worksheet()
    [ws.write(0, i, c) for i, c in enumerate(columns)]
    for i, ele in enumerate(data, start=1):
        for k, v in ele.items():
            ws.write(i, columns.index(k), v)
    wb.close()