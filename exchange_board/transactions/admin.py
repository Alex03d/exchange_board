from django.contrib import admin
from .models import Transaction


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


admin.site.register(Transaction, TransactionAdmin)
