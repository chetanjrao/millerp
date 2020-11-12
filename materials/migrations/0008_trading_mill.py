# Generated by Django 3.0.6 on 2020-11-12 02:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_mill_owner'),
        ('materials', '0007_auto_20201111_1821'),
    ]

    operations = [
        migrations.AddField(
            model_name='trading',
            name='mill',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.PROTECT, to='core.Mill'),
            preserve_default=False,
        ),
    ]
