# Generated by Django 3.0.6 on 2020-12-28 03:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0018_productsale'),
    ]

    operations = [
        migrations.AddField(
            model_name='productsale',
            name='remarks',
            field=models.TextField(null=True),
        ),
    ]
