# Generated by Django 5.1.4 on 2025-01-27 16:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_remove_quote_accessor_usermodel_preference_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bid',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bids', to='core.client'),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField()),
                ('currency', models.CharField(default='usd', max_length=10)),
                ('stripe_payment_id', models.CharField(max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assessor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='core.accessor')),
                ('bid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='core.bid')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='core.client')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='core.job')),
            ],
        ),
    ]
