# Generated by Django 3.0.6 on 2020-11-24 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0014_auto_20201124_1332'),
    ]

    operations = [
        migrations.AddField(
            model_name='productiontype',
            name='is_external',
            field=models.BooleanField(default=False),
        ),
    ]
