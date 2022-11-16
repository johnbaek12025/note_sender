from ast import keyword
from django.db import models



class Bloger(models.Model):
    class Meta:
        ordering = ["-birth"]
        
    bid = models.CharField(max_length=200, unique=True)    
    blog_name = models.CharField(max_length=200, blank=True, null=True)
    birth = models.DateTimeField(auto_now_add=True)
    keyword = models.CharField(max_length=200, blank=True, null=True)
