# Generated by Django 3.0.6 on 2020-11-27 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0015_productiontype_is_external'),
    ]

    operations = [
        migrations.AddField(
            model_name='productiontype',
            name='is_biproduct',
            field=models.BooleanField(default=False),
        ),
    ]
