from django.urls import path, include
from devoperator.views.response import NoteDataView, account_check, gather_taker, logout, sweep_data

app_name = 'devoperator'

urlpatterns = [
    path('', NoteDataView.as_view()),
    path('collect/', gather_taker, name='collect'),
    path('data_delete/', sweep_data, name='data_delete'),
    path('account_check/', account_check, name='account_check'),
    path('logout/', logout, name='logout'),
]