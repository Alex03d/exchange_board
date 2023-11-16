from django.contrib import admin

from .models import TransactionComment


@admin.register(TransactionComment)
class TransactionCommentAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'author', 'content', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'author__username', 'transaction__id')
    raw_id_fields = ('author', 'transaction')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
