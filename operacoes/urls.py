from django.urls import path
from . import views

urlpatterns = [
    # Tela única: escolher vendedor + tipo (REMESSA / RECEBIMENTO)
    path('operacao/nova/', views.operacao_nova, name='operacao_nova'),

    # Detalhe da remessa (pós-salvar)
    path('remessas/<int:pk>/', views.remessa_detail, name='remessa_detail'),
]
