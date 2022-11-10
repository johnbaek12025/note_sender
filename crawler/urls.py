from django.urls import path
from crawler.views import SendCrawler


app_name = 'clawler'

urlpatterns = [    
    path('send/get/', SendCrawler.as_view()),
    path('send/post/', SendCrawler.as_view()),
]