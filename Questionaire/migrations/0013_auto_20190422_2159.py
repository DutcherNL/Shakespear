# Generated by Django 2.1.5 on 2019-04-22 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0012_auto_20190422_1606'),
    ]

    operations = [
        migrations.AddField(
            model_name='technology',
            name='long_text',
            field=models.TextField(default='empty'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='technology',
            name='short_text',
            field=models.CharField(default='empty', max_length=256),
            preserve_default=False,
        ),
    ]
