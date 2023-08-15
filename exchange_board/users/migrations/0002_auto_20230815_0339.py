# Generated by Django 2.2.19 on 2023-08-15 03:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='mnt_transfer_data',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='rub_transfer_data',
        ),
        migrations.RemoveField(
            model_name='customuser',
            name='usd_transfer_data',
        ),
        migrations.AddField(
            model_name='customuser',
            name='invited_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referrals', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='customuser',
            name='mnt_account_or_phone',
            field=models.CharField(blank=True, help_text='Account or Phone for Tugrik transfers', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='mnt_bank_name',
            field=models.CharField(blank=True, help_text='Bank Name for Tugrik transfers', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='mnt_recipient_name',
            field=models.CharField(blank=True, help_text='Recipient Name for Tugrik transfers', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='rub_account_or_phone',
            field=models.CharField(blank=True, help_text='Account or Phone for Ruble transfers', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='rub_bank_name',
            field=models.CharField(blank=True, help_text='Bank Name for Ruble transfers', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='rub_recipient_name',
            field=models.CharField(blank=True, help_text='Recipient Name for Ruble transfers', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='usd_account_or_phone',
            field=models.CharField(blank=True, help_text='Account or Phone for USD transfers', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='usd_bank_name',
            field=models.CharField(blank=True, help_text='Bank Name for USD transfers', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='usd_recipient_name',
            field=models.CharField(blank=True, help_text='Recipient Name for USD transfers', max_length=255, null=True),
        ),
    ]
