# Generated by Django 3.0.6 on 2020-11-10 14:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_productstock'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stock',
            name='quantity',
        ),
    ]
