# Generated by Django 2.2.19 on 2023-11-02 04:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bank_details', '0002_bankdetail_user'),
        ('offers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestfortransaction',
            name='applicant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='requestfortransaction',
            name='bank_detail',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='related_requests', to='bank_details.BankDetail'),
        ),
        migrations.AddField(
            model_name='requestfortransaction',
            name='offer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests_for_transaction', to='offers.Offer'),
        ),
        migrations.AddField(
            model_name='offer',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='offer',
            name='bank_detail',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='related_offers', to='bank_details.BankDetail'),
        ),
        migrations.AddField(
            model_name='offer',
            name='currency_needed',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offers_needed', to='bank_details.Currency'),
        ),
        migrations.AddField(
            model_name='offer',
            name='currency_offered',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offers_offered', to='bank_details.Currency'),
        ),
        migrations.AlterUniqueTogether(
            name='requestfortransaction',
            unique_together={('offer', 'applicant')},
        ),
    ]