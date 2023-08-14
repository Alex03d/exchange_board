from django.contrib import admin
from .models import CustomUser, Invitation


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'invites_left', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('date_joined',)


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('code', 'inviter', 'used')
    search_fields = ('code', 'inviter__username')
    list_filter = ('used',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Invitation, InvitationAdmin)
