# Generated by Django 4.0.3 on 2022-04-20 05:14

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Driver',
            fields=[
                ('name', models.CharField(max_length=500, primary_key=True, serialize=False, unique=True)),
                ('status', models.IntegerField(blank=True, default=0)),
                ('myorder_id', models.IntegerField(default=-1)),
                ('product', models.IntegerField(blank=True, default=0)),
                ('lat', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10)),
                ('lon', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mypassenger', models.CharField(max_length=500)),
                ('mydriver', models.CharField(max_length=500)),
                ('origin_name', models.CharField(blank=True, default='0', max_length=50)),
                ('origin_lat', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10)),
                ('origin_lon', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10)),
                ('dest_name', models.CharField(blank=True, default='0', max_length=50)),
                ('dest_lat', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10)),
                ('dest_lon', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10)),
                ('match_time', models.FloatField(blank=True, default=0)),
                ('start_time', models.FloatField(default=0)),
                ('end_time', models.FloatField(blank=True, default=0)),
                ('product', models.IntegerField(blank=True, default=0)),
                ('status', models.IntegerField(blank=True, default=0)),
                ('money', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Passenger',
            fields=[
                ('name', models.CharField(max_length=500, primary_key=True, serialize=False, unique=True)),
                ('status', models.IntegerField(blank=True, default=0)),
                ('myorder_id', models.IntegerField(default=-1)),
                ('product', models.IntegerField(blank=True, default=0)),
                ('lat', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10)),
                ('lon', models.DecimalField(blank=True, decimal_places=6, default=0, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=100)),
                ('price_per_meter', models.FloatField(default=0.002)),
                ('speed', models.FloatField(default=1.0)),
            ],
        ),
        migrations.CreateModel(
            name='SessionId',
            fields=[
                ('sessId', models.CharField(max_length=500, primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=500, unique=True)),
                ('job', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('products', models.CharField(default='', max_length=1000)),
            ],
        ),
    ]
