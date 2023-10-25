from django.contrib import admin
from .models import Offer, RequestForTransaction, Transaction


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


class RequestForTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'offer', 'applicant', 'applied_date', 'status'
    )
    list_filter = (
        'applied_date',
        'status'
    )
    search_fields = (
        'offer__author__username',
        'applicant__username'
    )


class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'offer', 'accepting_user', 'status'
    )
    list_filter = (
        'status',
    )
    search_fields = (
        'offer__author__username',
        'accepting_user__username'
    )


admin.site.register(Offer, OfferAdmin)
admin.site.register(RequestForTransaction, RequestForTransactionAdmin)
admin.site.register(Transaction, TransactionAdmin)
