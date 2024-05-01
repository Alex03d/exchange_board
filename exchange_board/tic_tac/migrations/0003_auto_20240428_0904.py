# Generated by Django 2.2.19 on 2024-04-28 01:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tic_tac', '0002_auto_20240427_0718'),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('board', models.CharField(default='         ', max_length=9)),
                ('current_player', models.CharField(default='X', max_length=1)),
            ],
        ),
        migrations.DeleteModel(
            name='TicTacToeGame',
        ),
    ]