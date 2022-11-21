
from devoperator.tasks.login_request import NaverLogin
from devoperator.views.exception import CheckingError, LoginError


class NoteSender(NaverLogin):
    def __init__(self, **kwargs):
        super()      
        self.session = kwargs['session']
        self.check_count_urls = "https://note.naver.com/json/write/"
        self.note_send_url = "https://note.naver.com/json/write/send/"
        self.data = {
            "svcType": "undefined",
            "svcId": None,
            "svcName": None,
            'content': kwargs.get('msg'),
            "isReplyNote": 0,
            "targetUserId": kwargs.get('taker'),
            "isBackup": 1,
            "u": None
        }
        self.sender = None
    
    def _set_token(self):
        tokens = self.status_validation(self.check_count_urls, self.session, post_data=self.data)
        self.data.update({"token": tokens['token'], "svcCode": tokens['svcCode']})

    def check_note_count(self):
        try:
            res = self.status_validation(self.check_count_urls, self.session)
        except LoginError:            
            raise LoginError
        else:
            self.data['u'] = res['userId']
            print(res)
            return res
    
    def sending(self):
        if not self.check_note_count():
            raise CheckingError
        self._set_token()        
        res = self.status_validation(self.note_send_url, self.session, post_data=self.data)        
        print(res)
        if res['Result'] == 'FAIL':
            print('Failed Sending')
        else:
            print(res['Message'])    