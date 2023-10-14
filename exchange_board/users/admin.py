from django.contrib import admin
from .models import CustomUser, Invitation, Currency, BankDetail, UserFollow, EmailConfirmation

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'invites_left', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('date_joined',)


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('code', 'inviter', 'used')
    search_fields = ('code', 'inviter__username')
    list_filter = ('used',)


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


class BankDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'bank_name', 'account_or_phone', 'recipient_name')
    search_fields = ('user__username', 'currency__code')
    list_filter = ('currency',)


class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')


class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ('user', 'confirmation_token', 'timestamp', 'confirmed')
    search_fields = ('user__username', 'confirmation_token')
    list_filter = ('confirmed',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Invitation, InvitationAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(BankDetail, BankDetailAdmin)
admin.site.register(UserFollow, UserFollowAdmin)
admin.site.register(EmailConfirmation, EmailConfirmationAdmin)
