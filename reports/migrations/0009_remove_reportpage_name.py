# Generated by Django 3.0 on 2020-02-07 11:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_auto_20200204_1517'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reportpage',
            name='name',
        ),
    ]
