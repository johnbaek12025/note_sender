from datetime import timedelta
import functools
from django.http import HttpResponse
from django.db.models import QuerySet, Model
from django.forms import model_to_dict
import json
from django.utils.timezone import now
from django.views import View
from numpy import kaiser

from devoperator.views.exception import NotParsedError, SessionCookieNonExists, SessionExpiration, SessionValueWrong


class HttpResponseBase(HttpResponse):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._headers = self.headers 

class BaseJsonFormat:

    def __init__(self, *, msg=None, is_success=True, error_msg=None, data: list = None):
        self.is_success = is_success
        self.msg = msg
        self.error_msg = error_msg
        self.data = data

    def __str__(self):

        return json.dumps(self.__dict__)

class BasicJsonResponse(HttpResponseBase):

    def __init__(self, *, is_success: bool = True, status: int = 200, data=None, msg=None, error_msg=None, **kwargs):

        json_content = dict()
        json_content['is_success'] = is_success
        '''""{"date": , "content": }""'''

        if msg is not None:
            json_content['msg'] = msg
        if error_msg is not None:
            json_content['error_msg'] = error_msg

        if status is None:
            if is_success:
                status = 200
            else:
                raise Exception("status 값을 입력해야합니다.")   # todo: custom exception class

        if data is not None:
            if type(data) is QuerySet:
                json_content['data'] = list(data.values())
            elif isinstance(data, Model):
                json_content['data'] = model_to_dict(data)
            else:
                json_content['data'] = data

        super().__init__(json.dumps(json_content, default=str, ensure_ascii=False), content_type="application/json; charset=utf-8", status=status, **kwargs)

