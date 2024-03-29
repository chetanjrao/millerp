# Generated by Django 3.0.6 on 2020-11-23 10:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20201123_0517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cmr',
            name='bora',
            field=models.FloatField(),
        ),
        migrations.CreateModel(
            name='cmr_entry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bags', models.FloatField()),
                ('price', models.FloatField()),
                ('is_deleted', models.BooleanField(default=False)),
                ('cmr', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.cmr')),
                ('truck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Truck')),
            ],
        ),
    ]
