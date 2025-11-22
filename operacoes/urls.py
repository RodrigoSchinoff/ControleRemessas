# operacoes/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('operacao/nova/', views.operacao_nova, name='operacao_nova'),
    path('remessa/<int:pk>/', views.remessa_detail, name='remessa_detail'),
    path(
        'remessas/vendedor/<int:vendedor_id>/',
        views.remessas_por_vendedor,
        name='remessas_por_vendedor',
    ),
    path(
        'recebimentos/vendedor/<int:vendedor_id>/',
        views.recebimentos_por_vendedor,
        name='recebimentos_por_vendedor',
    ),
]
