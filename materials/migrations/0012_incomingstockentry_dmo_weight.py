# Generated by Django 3.0.6 on 2020-12-13 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0011_customer_sale'),
    ]

    operations = [
        migrations.AddField(
            model_name='incomingstockentry',
            name='dmo_weight',
            field=models.FloatField(default=0),
        ),
    ]
