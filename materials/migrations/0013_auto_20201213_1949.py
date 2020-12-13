# Generated by Django 3.0.6 on 2020-12-13 14:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_auto_20201208_1205'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('materials', '0012_incomingstockentry_dmo_weight'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('mill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Mill')),
            ],
        ),
        migrations.AddField(
            model_name='incomingstockentry',
            name='bag',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='materials.Bag'),
        ),
    ]
