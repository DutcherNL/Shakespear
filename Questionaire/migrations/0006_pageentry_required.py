# Generated by Django 2.1.5 on 2019-03-14 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0005_auto_20190312_1227'),
    ]

    operations = [
        migrations.AddField(
            model_name='pageentry',
            name='required',
            field=models.BooleanField(default=False),
        ),
    ]