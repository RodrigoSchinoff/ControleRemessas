from django.urls import path
from . import views

urlpatterns = [
    # Tela única: escolher vendedor + tipo (REMESSA / RECEBIMENTO)
    path('operacao/nova/', views.operacao_nova, name='operacao_nova'),

    # Detalhe da remessa (pós-salvar)
    path('remessas/<int:pk>/', views.remessa_detail, name='remessa_detail'),

# >>> NOVA ROTA adicionada sem alterar as existentes <<<
    path('remessas/vendedor/<int:vendedor_id>/', views.remessas_por_vendedor, name='remessas_por_vendedor'),

]
