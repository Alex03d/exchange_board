from django.contrib import admin

from .models import ExchangeRate


class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = (
        'usd_to_rub',
        'mnt_to_rub',
        'mnt_to_usd',
        'date_updated'
    )
    list_filter = ('date_updated',)
    search_fields = ('date_updated',)


admin.site.register(ExchangeRate, ExchangeRateAdmin)
