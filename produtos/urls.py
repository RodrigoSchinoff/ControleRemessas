# produtos/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.produtos_list, name='produtos_list'),
]
