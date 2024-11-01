# Generated by Django 2.2.19 on 2023-11-02 04:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(choices=[('USD', 'US Dollar'), ('RUB', 'Russian Ruble'), ('MNT', 'Mongolian Tugrik')], max_length=3, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('help_text_template', models.CharField(help_text="Template for the help text, e.g., 'Bank Name for {currency_name} transfers'", max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='BankDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bank_name', models.CharField(blank=True, max_length=255, null=True)),
                ('account_or_phone', models.CharField(blank=True, max_length=255, null=True)),
                ('recipient_name', models.CharField(blank=True, max_length=255, null=True)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bank_details.Currency')),
            ],
        ),
    ]
