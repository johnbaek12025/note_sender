from django.urls import path

from devoperator.views import AddMsg, AddQ, AddTrs, AssignAccounts, SendNote, check_account, download_account_excel, main_page

app_name = 'devoperator'

urlpatterns = [
    path('', main_page),
    path('note/', SendNote.as_view()),
    path('log/', SendNote.as_view()),
    path('account/', AssignAccounts.as_view()),
    path('account/excel/download', download_account_excel),
    path('account/check/', check_account),
    path('account/register/', AssignAccounts.as_view()),
    path('account/delete/', AssignAccounts.as_view()),
    path('account/update/<int:id>/', AssignAccounts.as_view()),
    path('msg/', AddMsg.as_view()),
    path('msg/modify/', AddMsg.as_view()),
    path('msg/register/', AddMsg.as_view()),
    path('quote/', AddQ.as_view()),
    path('quote/modify/', AddQ.as_view()),
    path('quote/register/', AddQ.as_view()),
    path('transition/', AddTrs.as_view()),
    path('transition/modify/', AddTrs.as_view()),
    path('transition/register/', AddTrs.as_view()),
    path('data/delete/', main_page)    
]