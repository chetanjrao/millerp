# Generated by Django 3.0.6 on 2020-11-09 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OTP',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mobile', models.CharField(max_length=16)),
                ('otp', models.CharField(max_length=4)),
                ('created_at', models.DateTimeField(auto_now=True, null=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'OTP',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.IntegerField(choices=[(1, 'Staff'), (2, 'Mill Manager'), (3, 'Owner'), (4, 'Support Staff'), (5, 'Administrator')], default=3),
        ),
    ]