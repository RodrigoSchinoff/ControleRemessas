# controle_remessas/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from produtos.views import produto_create
from core.views import home
from vendedores.views import vendedores_list, vendedor_create  # ✅ importar daqui

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticação
    path('accounts/login/',  auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Home / Redirect
    path('', RedirectView.as_view(pattern_name='home', permanent=False)),
    path('home/', home, name='home'),

    # Vendedores (lista + cadastro pelo próprio usuário)
    path('vendedores/', vendedores_list, name='vendedores_list'),
    path('vendedores/novo/', vendedor_create, name='vendedor_create'),

    path('produtos/novo/', produto_create, name='produto_create'),
    path('produtos/', include('produtos.urls')),

    # Operações (remessa/recebimento)
    path('operacoes/', include('operacoes.urls')),

    path(
        'logout/',
        auth_views.LogoutView.as_view(
            next_page='/accounts/login/',
            http_method_names=['get', 'post']
        ),
        name='logout'
    ),

]
