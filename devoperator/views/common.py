from datetime import timedelta
import functools
from django.http import HttpResponse
from django.db.models import QuerySet, Model
from django.forms import model_to_dict
import json
from django.utils.timezone import now
from django.views import View
from numpy import kaiser
from devoperator.models import LoginSession
from devoperator.utility.utility import who_are_you

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

class ParsedClientView(View):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = None

    @staticmethod
    def init_parse(fun):

        @functools.wraps(fun)
        def wrapper(*args, **kwargs):
            
            instance = args[0]
            req = kwargs.get('req', None) or args[1]  # self -> 0, req -> 1
            try:
                client_obj = get_client_object(req=req)
            except (SessionCookieNonExists, SessionValueWrong):
                # 세션없음
                res = BaseJsonFormat(is_success=False, error_msg='세션이 없거나 잘못된 세션값입니다.')
                res = HttpResponse(res, content_type="application/json", status=401)
                return res
            else:
                setattr(instance, '_client', client_obj)
            return fun(*args, **kwargs)

        return wrapper

    def set_default_page_context(self, context: dict):

        context.update({
            'client_name': self.client.name,
        })
    @property
    def client(self):
        if self._client is None:
            return None
        return self._client


def get_client_object(account=None, req=None, session_birth_within=7):

    if (account, req) == (None, None):
        raise ValueError('account, req 둘 중 최소 하나는 입력해줘야 합니다.')

    if req and account is None:
        try:
            login_session_value = req.COOKIES['login']
        except KeyError:
            raise SessionCookieNonExists
        else:
            try:
                login_session = LoginSession.objects.get(value=login_session_value, logged_out=False)
                account = login_session.account
            except LoginSession.DoesNotExist:
                raise SessionValueWrong
            else:
                try:
                    login_session = LoginSession.objects.get(
                        value=login_session_value,
                        birth__gte=now()-timedelta(days=session_birth_within)
                    )
                except LoginSession.DoesNotExist:
                    raise SessionExpiration

    who = who_are_you(account)
    return who