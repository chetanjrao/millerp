# Generated by Django 3.0.6 on 2020-11-14 03:09

from django.db import migrations, models
import django.db.models.deletion
import fernet_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_mill_owner'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mill',
            name='mill_password',
        ),
        migrations.RemoveField(
            model_name='mill',
            name='mill_username',
        ),
        migrations.CreateModel(
            name='Firm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('username', fernet_fields.fields.EncryptedCharField(blank=True, max_length=64, null=True)),
                ('password', fernet_fields.fields.EncryptedCharField(blank=True, max_length=64, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('mill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Mill')),
            ],
        ),
    ]
