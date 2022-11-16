from django.db import models
from django.utils.timezone import now


class NaverAccounts(models.Model):
    class Meta:
        ordering = ["-birth"]
    birth = models.DateTimeField(auto_now_add=True)
    nid = models.CharField(max_length=200, unique=True)
    npw = models.CharField(max_length=200)    
    modified_at = models.DateTimeField(auto_now=True)
    validation = models.BooleanField(default=False)
    
    


class NoteSendingLog(models.Model):
    class Meta:
        ordering = ["-try_at"]
    birth = models.DateTimeField(db_index=True, auto_now_add=True)
    account = models.ForeignKey('NaverAccounts', on_delete=models.CASCADE)    
    is_success = models.BooleanField(default=False)
    error_msg = models.TextField(null=True, default=None, blank=True)
    try_at = models.CharField(max_length=20, null=True)
    try_at_date = models.CharField(max_length=10, null=True)
    msg = models.TextField()
    receiver = models.ForeignKey('crawler.Bloger', on_delete=models.CASCADE)
    

class Message(models.Model):
    msg = models.TextField()
    birth = models.DateTimeField(auto_now_add=True)
    


class Quote(models.Model):
    qut = models.TextField()
    birth = models.DateTimeField(auto_now_add=True)
    
    