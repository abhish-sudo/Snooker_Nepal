from django.urls import path
from . import views

app_name = 'tournaments'

urlpatterns = [
    path('',          views.tournament_list,   name='list'),
    path('submit/',   views.submit_tournament, name='submit'),
    path('<int:pk>/', views.tournament_detail, name='detail'),
]