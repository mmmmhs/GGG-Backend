# Generated by Django 4.0.3 on 2022-03-30 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GGG_backend', '0005_alter_driver_myorder'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sessionid',
            name='id',
        ),
        migrations.AlterField(
            model_name='sessionid',
            name='sessId',
            field=models.CharField(max_length=500, primary_key=True, serialize=False),
        ),
    ]
