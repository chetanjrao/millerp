# Generated by Django 3.0.6 on 2020-11-17 04:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0002_auto_20201114_1541'),
    ]

    operations = [
        migrations.AddField(
            model_name='bundle',
            name='mills',
            field=models.IntegerField(default=1),
        ),
    ]