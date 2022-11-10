from django.urls import path, include
from devoperator.views.response import NoteDataList

app_name = 'devoperator'

urlpatterns = [
    path('', NoteDataList.as_view()),
]