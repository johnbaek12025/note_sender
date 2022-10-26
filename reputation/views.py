from django.shortcuts import render
from django.http import HttpResponse
from django.conf.urls.static import static
from django.conf import settings

def home(req):
    print(settings.STATIC_ROOT)
    return render(req, 'main.html')
