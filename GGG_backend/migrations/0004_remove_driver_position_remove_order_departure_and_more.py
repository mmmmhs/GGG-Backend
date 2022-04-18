# Generated by Django 4.0.3 on 2022-04-18 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GGG_backend', '0003_driver_product_order_product_passenger_product'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='driver',
            name='position',
        ),
        migrations.RemoveField(
            model_name='order',
            name='departure',
        ),
        migrations.RemoveField(
            model_name='passenger',
            name='position',
        ),
        migrations.AddField(
            model_name='driver',
            name='lat',
            field=models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='driver',
            name='lon',
            field=models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='passenger',
            name='lat',
            field=models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='passenger',
            name='lon',
            field=models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10),
        ),
    ]
