from django.urls import path
from crawler.views import BlogerId, SendCrawler


app_name = 'clawler'

urlpatterns = [
    path('keyword/collect/', BlogerId.as_view(), name='keyword'),
    path('user/register/', BlogerId.as_view()),    
    path('', BlogerId.as_view()),
    path('delete/', BlogerId.as_view()),
    path('send/get/', SendCrawler.as_view()),
    path('send/post/', SendCrawler.as_view()),
]