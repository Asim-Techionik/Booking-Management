# Generated by Django 5.1.4 on 2025-01-27 16:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_bid_client_payment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bid',
            name='client',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='client',
        ),
    ]
