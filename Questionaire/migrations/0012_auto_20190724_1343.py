# Generated by Django 2.2 on 2019-07-24 11:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0011_auto_20190616_1452'),
    ]

    operations = [
        migrations.RenameField(
            model_name='question',
            old_name='validators',
            new_name='options',
        ),
    ]