from decimal import Decimal
from django.db.models import Sum
from vendedores.models import Vendedor
from produtos.models import Produto
from .models import Remessa, RemessaItem, Recebimento

ZERO = Decimal("0")

def total_remessas_reais(org, seller_id):
    """
    Soma de TODOS os itens de remessas do vendedor (valor R$).
    """
    tot = (RemessaItem.objects
           .filter(remessa__organization=org, remessa__seller_id=seller_id)
           .aggregate(s=Sum("total_item"))["s"])
    return tot or ZERO

def total_recebimentos_reais(org, seller_id, exclude_recebimento_id=None):
    """
    Soma de TODOS os recebimentos do vendedor (valor R$).
    Se exclude_recebimento_id for informado, exclui esse registro da soma (útil ao editar).
    """
    qs = Recebimento.objects.filter(organization=org, seller_id=seller_id)
    if exclude_recebimento_id:
        qs = qs.exclude(id=exclude_recebimento_id)
    tot = qs.aggregate(s=Sum("amount"))["s"]
    return tot or ZERO

def saldo_atual(org, seller_id, exclude_recebimento_id=None):
    """
    Saldo = total_remessas - total_recebimentos.
    Pode excluir um recebimento específico (edição).
    """
    return total_remessas_reais(org, seller_id) - total_recebimentos_reais(org, seller_id, exclude_recebimento_id)

def total_quantidade_remessas(org, seller_id):
    """
    Soma de TODAS as quantidades das remessas do vendedor (unidades).
    Usada para calcular qtd_equivalente no recebimento.
    """
    tot = (RemessaItem.objects
           .filter(remessa__organization=org, remessa__seller_id=seller_id)
           .aggregate(q=Sum("qty"))["q"])
    return Decimal(tot or 0)
