# Generated by Django 2.1.5 on 2019-11-15 10:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PageDisplay', '0006_auto_20191106_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagemodule',
            name='caption',
            field=models.CharField(blank=True, default='', max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='imagemodule',
            name='css',
            field=models.CharField(blank=True, default='', help_text='CSS classes in accordance with Bootstrap', max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='imagemodule',
            name='height',
            field=models.PositiveIntegerField(default=100),
        ),
    ]
