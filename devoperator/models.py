from django.db import models


class NaverAccounts(models.Model):
    class Meta:
        ordering = ["-birth"]

    birth = models.DateTimeField(auto_now_add=True)
    nid = models.CharField(max_length=200)
    npw = models.CharField(max_length=200)    
    modified_at = models.DateTimeField(auto_now_add=True)


class NoteSendingLog(models.Model):
    class Meta:
        ordering = ["-try_at"]

    account = models.ForeignKey('NaverAccounts', on_delete=models.CASCADE)
    ip = models.ForeignKey('Ip', on_delete=models.CASCADE)
    is_success = models.BooleanField(default=False)
    error_msg = models.TextField(null=True, default=None, blank=True)    
    try_at = models.DateTimeField(auto_now_add=True)
    try_at_date = models.CharField(db_index=True, max_length=10)
    msg = models.TextField()
    receivers = models.ForeignKey('crawler.Bloger', on_delete=models.CASCADE)
    

class Ip(models.Model):
    class Meta:
        ordering = ["-birth"]
    address = models.CharField(max_length=200)
    birth = models.DateTimeField(auto_now_add=True)    


class Message(models.Model):
    msg = models.TextField()
    birth = models.DateTimeField(auto_now_add=True)


class Transition(models.Model):
    msg = models.CharField(max_length=200)
    birth = models.DateTimeField(auto_now_add=True)


class Quote(models.Model):
    msg = models.TextField()
    birth = models.DateTimeField(auto_now_add=True)