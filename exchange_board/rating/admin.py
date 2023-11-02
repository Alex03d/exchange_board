from django.contrib import admin

from .models import Rating


class RatingAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'author', 'recipient', 'score', 'created_at')
    search_fields = ('author__username', 'recipient__username', 'transaction__id')
    list_filter = ('score', 'created_at')


admin.site.register(Rating, RatingAdmin)
