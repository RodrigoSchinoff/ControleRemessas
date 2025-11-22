from django.contrib import admin
from .models import Remessa, RemessaItem, Recebimento

class RemessaItemInline(admin.TabularInline):
    model = RemessaItem
    extra = 1

@admin.register(Remessa)
class RemessaAdmin(admin.ModelAdmin):
    list_display = ("id", "seller", "organization", "date")
    list_filter = ("organization", "seller")
    date_hierarchy = "date"
    inlines = [RemessaItemInline]

@admin.register(Recebimento)
class RecebimentoAdmin(admin.ModelAdmin):
    list_display = ("id", "seller", "organization", "date", "amount", "pct_sobre_saldo", "qtd_equivalente", "saldo_apos")
    list_filter = ("organization", "seller")
    date_hierarchy = "date"
