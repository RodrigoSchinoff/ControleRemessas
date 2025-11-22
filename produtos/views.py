# produtos/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import Produto


@login_required
def produto_create(request):
    """
    View usada pela tela 'Novo produto' (templates/produtos/produto_form.html)
    """
    org = request.current_org
    error = None

    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        if not name:
            error = 'Informe o nome do produto.'
        else:
            # Cria o produto vinculado à organização atual
            Produto.objects.create(
                organization=org,
                name=name,
            )
            # Depois de salvar, volta para a tela de operação (como o link 'Voltar')
            return redirect('operacao_nova')

    return render(request, 'produtos/produto_form.html', {
        'error': error,
    })


@login_required
def produtos_list(request):
    """
    Lista de produtos para o menu /produtos/
    """
    org = request.current_org
    produtos = Produto.objects.filter(organization=org).order_by('name')

    return render(request, 'produtos/produtos_list.html', {
        'produtos': produtos,
    })
