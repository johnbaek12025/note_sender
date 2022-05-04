from django.urls import path
from crawler.views import BlogerId


app_name = 'clawler'

urlpatterns = [
    path('keyword/collect/', BlogerId.as_view(), name='keyword'),
    path('user/register/', BlogerId.as_view()),    
    path('', BlogerId.as_view()),
    path('delete/', BlogerId.as_view()),
]