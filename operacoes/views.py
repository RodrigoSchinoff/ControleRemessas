# operacoes/views.py
from decimal import Decimal, ROUND_HALF_UP

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F

from .models import Remessa, RemessaItem, Recebimento
from vendedores.models import Vendedor
from produtos.models import Produto
from .forms import (
    CabecalhoOperacaoForm,
    RemessaCabecalhoForm,
    RemessaItemFormSet,
    RecebimentoForm,
)


def _q(v):
    if v is None:
        return Decimal('0.00')
    if not isinstance(v, Decimal):
        v = Decimal(str(v))
    return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _saldo_monetario(org, seller):
    total_remessas = RemessaItem.objects.filter(
        remessa__organization=org, remessa__seller=seller
    ).aggregate(v=Sum(F('qty') * F('unit_price')))['v'] or Decimal('0')
    total_receb = Recebimento.objects.filter(
        organization=org, seller=seller
    ).aggregate(v=Sum('amount'))['v'] or Decimal('0')
    return _q(total_remessas - total_receb)


def _saldo_quantidade(org, seller):
    total_qtd = RemessaItem.objects.filter(
        remessa__organization=org, remessa__seller=seller
    ).aggregate(v=Sum('qty'))['v'] or Decimal('0')
    total_qtd_rec = Recebimento.objects.filter(
        organization=org, seller=seller
    ).aggregate(v=Sum('qtd_equivalente'))['v'] or Decimal('0')
    return _q(total_qtd - total_qtd_rec)


def _preco_medio(org, seller):
    saldo_val = _saldo_monetario(org, seller)
    saldo_qtd = _saldo_quantidade(org, seller)
    if saldo_qtd <= 0:
        return Decimal('0')
    return _q(saldo_val / saldo_qtd)


@login_required
def operacao_nova(request):
    org = request.current_org
    sellers_qs = Vendedor.objects.filter(organization=org, is_active=True)


    # ---------------------------
    # POST = salvar Remessa/Recebimento
    # ---------------------------
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        seller_id = request.POST.get('seller')
        seller = get_object_or_404(Vendedor, pk=seller_id, organization=org)

        if tipo == 'REMESSA':
            print("DEBUG POST REMESSA - tipo:", tipo, "seller_id:", seller_id)
            rem_form = RemessaCabecalhoForm(request.POST)
            formset = RemessaItemFormSet(request.POST)
            for f in formset.forms:
                f.empty_permitted = True
                if 'product' in f.fields:
                    f.fields['product'].queryset = Produto.objects.filter(organization=org)

            if rem_form.is_valid() and formset.is_valid():
                remessa = rem_form.save(commit=False)
                remessa.organization = org
                remessa.seller = seller
                remessa.save()

                itens = formset.save(commit=False)
                for item in itens:
                    # ignora linhas vazias ou zeradas
                    if (item.product_id is None) and (not item.qty or item.qty == 0) and (
                            not item.unit_price or item.unit_price == 0):
                        continue
                    # ignora linhas incompletas
                    if not item.product_id or not item.qty or not item.unit_price:
                        continue

                    item.remessa = remessa
                    item.total_item = _q((item.qty or 0) * (item.unit_price or 0))
                    item.save()
                for obj in formset.deleted_objects:
                    obj.delete()

                return redirect('remessa_detail', pk=remessa.pk)

            # 👉 ADICIONE ESTES PRINTS ANTES DO RETURN
            print("ERROS REMESSA CAB:", rem_form.errors)
            print("ERROS FORMSET:", formset.errors)
            print("NON_FORM_ERRORS FORMSET:", formset.non_form_errors())

            # Reexibe com erros
            cab_form = CabecalhoOperacaoForm(initial={'seller': seller.pk, 'tipo': 'REMESSA'})
            cab_form.fields['seller'].queryset = sellers_qs
            return render(request, 'operacoes/operacao_nova.html', {
                'cab_form': cab_form,
                'mostrar_remessa': True,
                'rem_form': rem_form,
                'formset': formset,
                'seller_id': seller.pk,
                'tipo': 'REMESSA',
            })

        if tipo == 'RECEBIMENTO':
            # Logs para inspeção
            print("DEBUG POST RECEBIMENTO - tipo:", tipo, "seller_id:", seller_id)

            saldo_val = _saldo_monetario(org, seller)
            saldo_qtd = _saldo_quantidade(org, seller)
            preco_medio = _preco_medio(org, seller)
            print("DEBUG SALDOS RECEBIMENTO - saldo_val:", saldo_val,
                  "saldo_qtd:", saldo_qtd, "preco_medio:", preco_medio)

            # Instância já com organization e seller preenchidos
            receb_inst = Recebimento(organization=org, seller=seller)

            # O ModelForm usa essa instância, então o clean() já enxerga org e seller
            rec_form = RecebimentoForm(request.POST, instance=receb_inst)

            if rec_form.is_valid():
                receb = rec_form.save(commit=False)

                amount = _q(receb.amount)

                if amount > saldo_val:
                    rec_form.add_error(
                        'amount',
                        f'Valor excede o saldo do vendedor (R$ {saldo_val}).'
                    )
                elif preco_medio <= 0:
                    rec_form.add_error(
                        None,
                        'Não há saldo (ou preço médio = 0) para calcular a quantidade equivalente.'
                    )
                else:
                    receb.qtd_equivalente = _q(amount / preco_medio)
                    receb.pct_sobre_saldo = _q((amount / saldo_val) * 100) if saldo_val > 0 else Decimal('0')
                    receb.saldo_apos = _q(saldo_val - amount)
                    receb.save()
                    print("DEBUG RECEBIMENTO SALVO - id:", receb.id, "amount:", receb.amount)
                    return redirect('vendedores_list')

            # Se chegou aqui, houve erro de validação (do form ou das regras acima)
            print("ERROS RECEBIMENTO:", rec_form.errors, "NON_FIELD_ERRORS:", rec_form.non_field_errors())

            cab_form = CabecalhoOperacaoForm(initial={'seller': seller.pk, 'tipo': 'RECEBIMENTO'})
            cab_form.fields['seller'].queryset = sellers_qs
            return render(request, 'operacoes/operacao_nova.html', {
                'cab_form': cab_form,
                'mostrar_recebimento': True,
                'rec_form': rec_form,
                'saldo_info': {
                    'saldo_val': saldo_val,
                    'saldo_qtd': saldo_qtd,
                    'preco_medio': preco_medio,
                },
                'seller_id': seller.pk,
                'tipo': 'RECEBIMENTO',
            })

        # Tipo inválido → volta para seleção
        cab_form = CabecalhoOperacaoForm()
        cab_form.fields['seller'].queryset = sellers_qs
        return render(request, 'operacoes/operacao_nova.html', {'cab_form': cab_form})

    # ---------------------------
    # GET = seleção e render dinâmico (sem JS, com botão Continuar; com JS, auto-submit)
    # ---------------------------
    cab_form = CabecalhoOperacaoForm(request.GET or None)  # bind ao GET
    cab_form.fields['seller'].queryset = sellers_qs

    # sem ambos → só mostra seleção
    if not (cab_form.is_valid() and cab_form.cleaned_data.get('seller') and cab_form.cleaned_data.get('tipo')):
        return render(request, 'operacoes/operacao_nova.html', {'cab_form': cab_form})

    seller = cab_form.cleaned_data['seller']
    tipo = cab_form.cleaned_data['tipo']

    if tipo == 'REMESSA':
        rem_form = RemessaCabecalhoForm()
        formset = RemessaItemFormSet()
        for f in formset.forms:
            f.empty_permitted = True
            if 'product' in f.fields:
                f.fields['product'].queryset = Produto.objects.filter(organization=org)
        return render(request, 'operacoes/operacao_nova.html', {
            'cab_form': cab_form,
            'mostrar_remessa': True,
            'rem_form': rem_form,
            'formset': formset,
            'seller_id': seller.pk,
            'tipo': 'REMESSA',
        })

    # RECEBIMENTO
    rec_form = RecebimentoForm()
    saldo_val = _saldo_monetario(org, seller)
    saldo_qtd = _saldo_quantidade(org, seller)
    preco_medio = _preco_medio(org, seller)
    return render(request, 'operacoes/operacao_nova.html', {
        'cab_form': cab_form,
        'mostrar_recebimento': True,
        'rec_form': rec_form,
        'saldo_info': {
            'saldo_val': saldo_val,
            'saldo_qtd': saldo_qtd,
            'preco_medio': preco_medio,
        },
        'seller_id': seller.pk,
        'tipo': 'RECEBIMENTO',
    })


@login_required
def remessa_detail(request, pk):
    org = request.current_org
    remessa = get_object_or_404(Remessa, pk=pk, organization=org)
    itens = RemessaItem.objects.filter(remessa=remessa).select_related('product')
    total = sum((i.total_item or 0) for i in itens)
    return render(request, 'operacoes/remessa_detail.html', {
        'remessa': remessa,
        'itens': itens,
        'total': total,
    })

@login_required
def remessas_por_vendedor(request, vendedor_id):
    org = request.current_org
    vendedor = get_object_or_404(Vendedor, pk=vendedor_id, organization=org)

    remessas = Remessa.objects.filter(
        organization=org,
        seller=vendedor
    ).order_by('-date')

    return render(request, 'operacoes/remessas_por_vendedor.html', {
        'vendedor': vendedor,
        'remessas': remessas,
    })

@login_required
def recebimentos_por_vendedor(request, vendedor_id):
    org = request.current_org
    vendedor = get_object_or_404(Vendedor, pk=vendedor_id, organization=org)

    recebimentos = Recebimento.objects.filter(
        organization=org,
        seller=vendedor
    ).order_by('-date')

    return render(request, 'operacoes/recebimentos_por_vendedor.html', {
        'vendedor': vendedor,
        'recebimentos': recebimentos,
    })
