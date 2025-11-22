# vendedores/views.py
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F

from .models import Vendedor
from .forms import VendedorForm
from operacoes.models import RemessaItem, Recebimento


@login_required
def vendedores_list(request):
    """Lista vendedores da organization atual com saldo calculado."""
    org = request.current_org

    vendedores = Vendedor.objects.filter(
        organization=org
    ).order_by('name')

    # calcula e anexa o saldo em cada vendedor
    for v in vendedores:
        total_remessas = RemessaItem.objects.filter(
            remessa__organization=org,
            remessa__seller=v
        ).aggregate(v=Sum(F('qty') * F('unit_price')))['v'] or Decimal('0')

        total_receb = Recebimento.objects.filter(
            organization=org,
            seller=v
        ).aggregate(v=Sum('amount'))['v'] or Decimal('0')

        v_saldo = ((total_remessas or Decimal('0')) - (total_receb or Decimal('0'))).quantize(Decimal("0.01"))
        v.saldo = v_saldo
        v.saldo_fmt = format(v_saldo, ",.2f").replace(",", "#").replace(".", ",").replace("#", ".")

    return render(request, 'core/vendedores_list.html', {
        'vendedores': vendedores,
    })


@login_required
def vendedor_create(request):
    """Cadastro de vendedor vinculado à organization atual (sem admin)."""
    org = request.current_org
    next_url = request.GET.get('next') or request.POST.get('next') or None

    if request.method == 'POST':
        form = VendedorForm(request.POST)
        if form.is_valid():
            vend = form.save(commit=False)
            vend.organization = org
            vend.save()
            return redirect(next_url or 'operacao_nova')
    else:
        form = VendedorForm(initial={'is_active': True})

    return render(request, 'vendedores/vendedor_form.html', {
        'form': form,
        'next_url': next_url,
    })
