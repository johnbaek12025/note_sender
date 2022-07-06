from django.urls import path, include
from django.contrib.auth import views as auth_views
from devoperator.views.response import AddMsg, AddQ, AssignAccounts, BlogerId, CheckAccount, ExcelForm, SendNote, CheckAccount, Login

app_name = 'devoperator'

urlpatterns = [
    path('', Login.as_view(), name='login'),
    path('note/', SendNote.as_view()),
    path('log/', SendNote.as_view()),
    path('account/', AssignAccounts.as_view()),
    path('account/excel/download', ExcelForm.as_view()),
    path('account/check/', CheckAccount.as_view()),
    path('account/register/', AssignAccounts.as_view()),
    path('account/delete/', AssignAccounts.as_view()),
    path('account/update/<int:id>/', AssignAccounts.as_view()),
    path('keyword/collect/', BlogerId.as_view(), name='keyword'),
    path('receiver/register/', BlogerId.as_view()),    
    path('receiver/', BlogerId.as_view()),
    path('delete/', BlogerId.as_view()),
    path('msg/', AddMsg.as_view()),
    path('msg/modify/', AddMsg.as_view()),
    path('msg/register/', AddMsg.as_view()),
    path('quote/', AddQ.as_view()),
    path('quote/modify/', AddQ.as_view()),
    path('quote/register/', AddQ.as_view()),      
]