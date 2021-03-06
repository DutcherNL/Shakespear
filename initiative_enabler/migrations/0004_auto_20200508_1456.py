# Generated by Django 3.0 on 2020-05-08 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('initiative_enabler', '0003_auto_20200507_1413'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiatedcollective',
            name='is_open',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='collectiveapprovalresponse',
            name='message',
            field=models.TextField(blank=True, max_length=1200, null=True, verbose_name='Bericht aan de initiatiefnemer'),
        ),
    ]
