# Generated by Django 2.2.19 on 2023-11-02 03:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('offers', '0007_auto_20231102_0322'),
        ('users', '0004_delete_rating'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BankDetail',
        ),
        migrations.DeleteModel(
            name='Currency',
        ),
    ]
