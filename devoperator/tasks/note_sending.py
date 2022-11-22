
from devoperator.views.exception import CheckingError, LoginError
from devoperator.tasks.login_request import NaverLogin
from decouple import config


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

    def check_note_count(self):
        try:
            res = self.status_validation(self.check_count_urls, self.session)
        except LoginError:            
            raise LoginError
        else:
            self.data['u'] = res['userId']
            # print(res)
            return res
    
    def _set_token(self):
        tokens = self.status_validation(self.check_count_urls, self.session, post_data=self.data)
        self.data.update({"token": tokens['token'], "svcCode": tokens['svcCode']})

    def sending(self):
        if not self.check_note_count():
            raise CheckingError
        self._set_token()        
        res = self.status_validation(self.note_send_url, self.session, post_data=self.data)        
        return res
            
            
            
if __name__=='__main__':
    nid = config('nid')
    npw = config('npw')
    # switchIp2()    
    nl = NaverLogin(nid, npw)
    
    session = nl.login()
    
    s = NoteSender(session=session, taker = 'rascu', msg='get it out son it is the begininig of wisdom')
    s.sending()
    
    