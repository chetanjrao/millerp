# Generated by Django 3.0.6 on 2020-11-07 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0005_remove_outgoingstockentry_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incomingstockentry',
            name='bags',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='outgoingstockentry',
            name='bags',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='processingsideentry',
            name='bags',
            field=models.IntegerField(),
        ),
    ]
