# Generated by Django 3.0.6 on 2020-11-07 17:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0006_auto_20201107_1703'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='processingsideentry',
            name='category',
        ),
        migrations.AlterField(
            model_name='processingsideentry',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='processingsideentrys', to='materials.ProcessingSide'),
        ),
    ]
