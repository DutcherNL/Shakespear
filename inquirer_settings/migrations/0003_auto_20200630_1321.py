# Generated by Django 2.2.8 on 2020-06-30 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inquirer_settings', '0002_auto_20200630_0150'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pendingmailverifyer',
            name='attempts',
        ),
        migrations.AddField(
            model_name='pendingmailverifyer',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='pendingmailverifyer',
            name='code',
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AlterField(
            model_name='pendingmailverifyer',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
    ]