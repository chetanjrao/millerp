# Generated by Django 3.0.6 on 2020-11-15 14:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_firm_conversion'),
    ]

    operations = [
        migrations.AddField(
            model_name='mill',
            name='factor',
            field=models.FloatField(default=2271),
        ),
    ]