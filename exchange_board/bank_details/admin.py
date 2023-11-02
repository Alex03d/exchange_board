from django.contrib import admin

from .models import BankDetail, Currency


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


class BankDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'bank_name', 'account_or_phone', 'recipient_name')
    search_fields = ('user__username', 'currency__code')
    list_filter = ('currency',)


admin.site.register(Currency, CurrencyAdmin)
admin.site.register(BankDetail, BankDetailAdmin)
