from django.forms import ModelForm
from django import forms
from django.core.exceptions import NON_FIELD_ERRORS

from crawler.models import Bloger
from .models import *

class AccForm(ModelForm):
    prefix = 'AccForm'
    def __init__(self, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        self.fields['nid'].required = False
        self.fields['npw'].required = False
        
    class Meta:
        model = NaverAccounts
        fields = ['nid', 'npw']
        required=False
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "%(model_name)s's %(field_labels)s are not unique.",
            }
        }    

class RecForm(ModelForm):
    prefix = 'RecForm'
    def __init__(self, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        self.fields['bid'].required = False
        
    
    class Meta:
        model = Bloger
        fields = ['bid']
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "%(model_name)s's %(field_labels)s are not unique.",
            }
        }
        
class MsgForm(ModelForm):
    prefix = 'MsgForm'
    class Meta:
        model = Message
        fields = ['msg']

class QutForm(ModelForm):
    prefix = 'QutForm'
    def __init__(self, *args, **kwargs):        
        super().__init__(*args, **kwargs)
        self.fields['qut'].required = False
        
    class Meta:
        model = Quote
        fields = ['qut']