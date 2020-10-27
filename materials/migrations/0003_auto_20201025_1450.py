# Generated by Django 3.1.2 on 2020-10-25 14:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0002_incomingstockentry_outgoingstockentry_processingsideentry'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='outgoingstockentry',
            name='average_weight',
        ),
        migrations.RemoveField(
            model_name='processingsideentry',
            name='average_weight',
        ),
        migrations.AlterField(
            model_name='processingsideentry',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='processingstockentrys', to='materials.processingside'),
        ),
    ]