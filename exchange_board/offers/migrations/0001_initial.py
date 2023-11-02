# Generated by Django 2.2.19 on 2023-11-02 04:46

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Offer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_offered', models.DecimalField(decimal_places=2, max_digits=15)),
                ('publishing_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('open', 'Open'), ('PENDING', 'Pending'), ('in progress', 'In Progress'), ('closed', 'Closed')], default='open', max_length=11)),
            ],
        ),
        migrations.CreateModel(
            name='RequestForTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('applied_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10)),
            ],
        ),
    ]
