class Error(Exception):
    pass

class DatabaseError(Error):
    pass
class IntegrityError(DatabaseError):
    pass

class SessionError(Exception):
    pass

class SessionCookieNonExists(SessionError):
    pass

class SessionValueWrong(SessionError):
    pass
class SessionExpiration(SessionError):
    pass

class NotParsedError(Exception):
    pass

class LoginError(Exception):
    pass

class CheckingError(Exception):
    pass
