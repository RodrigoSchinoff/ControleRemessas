from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import Organization
from vendedores.models import Vendedor
from produtos.models import Produto

from decimal import Decimal
from django.core.exceptions import ValidationError

class Remessa(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    seller = models.ForeignKey(Vendedor, on_delete=models.PROTECT, related_name="remessas")
    date = models.DateField()
    obs = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Remessa #{self.id} - {self.seller.name}"

class RemessaItem(models.Model):
    remessa = models.ForeignKey(Remessa, on_delete=models.CASCADE, related_name="itens")
    product = models.ForeignKey(Produto, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField(blank=True, null=True)  # sem MinValueValidator
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    total_item = models.DecimalField(max_digits=14, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # total_item = qty * unit_price
        self.total_item = (self.qty or 0) * (self.unit_price or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x{self.qty}"

class Recebimento(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, db_index=True)
    seller = models.ForeignKey(Vendedor, on_delete=models.PROTECT, related_name="recebimentos")
    date = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0.01)])
    # informativos
    pct_sobre_saldo = models.DecimalField(max_digits=6, decimal_places=4, default=0)      # ex.: 0.4000 = 40%
    qtd_equivalente = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    saldo_apos = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return f"Recebimento #{self.id} - {self.seller.name}"

    def clean(self):
        # organization e seller são obrigatórios e coerentes
        from .services import saldo_atual

        if not self.organization_id or not self.seller_id:
            raise ValidationError("Organization e vendedor são obrigatórios.")

        # Saldo antes deste recebimento (excluindo ele próprio se for edição)
        saldo_antes = saldo_atual(self.organization, self.seller_id, exclude_recebimento_id=self.id)
        if self.amount is None or self.amount <= 0:
            raise ValidationError("Valor do recebimento deve ser maior que zero.")
        if self.amount > saldo_antes:
            raise ValidationError("Valor recebido não pode exceder o saldo em aberto.")

    def save(self, *args, **kwargs):
        # Recalcula snapshot informativo no momento da gravação
        from .services import saldo_atual, total_quantidade_remessas  # import local para evitar ciclos

        saldo_antes = saldo_atual(self.organization, self.seller_id, exclude_recebimento_id=self.id)
        if saldo_antes <= 0:
            # Sem saldo, normalize informativos
            self.pct_sobre_saldo = Decimal("0")
            self.qtd_equivalente = Decimal("0")
            self.saldo_apos = Decimal("0")
        else:
            pct = (self.amount / saldo_antes) if saldo_antes > 0 else Decimal("0")
            total_qty = total_quantidade_remessas(self.organization, self.seller_id)
            qtd_eq = pct * total_qty

            self.pct_sobre_saldo = pct.quantize(Decimal("0.0001"))  # 4 casas para percentual
            self.qtd_equivalente = qtd_eq.quantize(Decimal("0.01"))  # 2 casas para unidades
            self.saldo_apos = (saldo_antes - self.amount).quantize(Decimal("0.01"))

        super().save(*args, **kwargs)
