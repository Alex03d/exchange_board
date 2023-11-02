from django.contrib import admin

from .models import RequestForTransaction


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


admin.site.register(RequestForTransaction, RequestForTransactionAdmin)
