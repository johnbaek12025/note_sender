from django.urls import path, include
from devoperator.views.response import NoteDataView, sweep_taker

app_name = 'devoperator'

urlpatterns = [
    path('', NoteDataView.as_view()),
    path('collect/', sweep_taker, name='collect')
]