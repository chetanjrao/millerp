# Generated by Django 3.0.6 on 2020-11-14 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='city',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='country',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='countrycode',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='state',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
