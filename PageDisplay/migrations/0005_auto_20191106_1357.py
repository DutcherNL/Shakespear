# Generated by Django 2.1.5 on 2019-11-06 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PageDisplay', '0004_auto_20190907_1908'),
    ]

    operations = [
        migrations.AddField(
            model_name='textmodule',
            name='css',
            field=models.CharField(blank=True, default='', help_text='CSS classes in accordance with Bootstrap', max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='titlemodule',
            name='css',
            field=models.CharField(blank=True, default='', help_text='CSS classes in accordance with Bootstrap', max_length=256, null=True),
        ),
    ]