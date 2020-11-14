# Generated by Django 3.0.6 on 2020-11-14 09:50

from django.db import migrations
import fernet_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20201114_0309'),
    ]

    operations = [
        migrations.AddField(
            model_name='firm',
            name='agreement_no',
            field=fernet_fields.fields.EncryptedField(default='', max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='firm',
            name='password',
            field=fernet_fields.fields.EncryptedCharField(max_length=64),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='firm',
            name='username',
            field=fernet_fields.fields.EncryptedCharField(max_length=64),
            preserve_default=False,
        ),
    ]