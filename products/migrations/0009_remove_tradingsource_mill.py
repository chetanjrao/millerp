# Generated by Django 3.0.6 on 2020-11-13 07:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_auto_20201113_0620'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tradingsource',
            name='mill',
        ),
    ]