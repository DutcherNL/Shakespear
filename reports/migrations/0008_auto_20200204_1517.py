# Generated by Django 3.0 on 2020-02-04 14:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('PageDisplay', '0011_imagemodule_mode'),
        ('reports', '0007_auto_20200204_1516'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='A4_PageContainer',
            new_name='PageContainer',
        ),
    ]
