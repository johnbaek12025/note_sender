from django.forms import ModelForm
from django import forms
from .models import *

class AccForm(ModelForm):
    nid = forms.CharField(max_length=200, label="네이버 아이디", error_messages={'required': "네이버 계정 입력"})
    npw = forms.CharField(max_length=200, label="네이버 비번", error_messages={'required': "네이버 비번 입력"})
    
    class Meta:
        model = NaverAccounts
        fields = ['nid', 'npw']
