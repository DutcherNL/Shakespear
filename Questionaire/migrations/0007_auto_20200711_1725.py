# Generated by Django 2.2.8 on 2020-07-11 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0006_auto_20200705_2336'),
    ]

    operations = [
        migrations.AddField(
            model_name='technology',
            name='display_in_step_1_list',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='technology',
            name='display_in_step_2_list',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='technology',
            name='display_in_step_3_list',
            field=models.BooleanField(default=False),
        ),
    ]
