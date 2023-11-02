from django.contrib import admin

from .models import Offer


class OfferAdmin(admin.ModelAdmin):
    list_display = (
        'author', 'amount_offered', 'currency_offered',
        'currency_needed', 'publishing_date', 'status'
    )
    list_filter = (
        'status',
        'publishing_date',
        'currency_offered',
        'currency_needed'
    )
    search_fields = (
        'author__username',
        'currency_offered',
        'currency_needed'
    )


admin.site.register(Offer, OfferAdmin)
