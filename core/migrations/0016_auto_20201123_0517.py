# Generated by Django 3.0.6 on 2020-11-23 05:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_cmr'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cmr',
            name='bora',
            field=models.IntegerField(),
        ),
    ]
