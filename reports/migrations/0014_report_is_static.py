# Generated by Django 2.2.8 on 2021-04-03 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0013_renderedreport'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='is_static',
            field=models.BooleanField(default=False, help_text='Whether the report is custom for each inquiry'),
        ),
    ]
