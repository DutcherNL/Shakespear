# Generated by Django 2.2.8 on 2020-07-12 13:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0008_auto_20200711_1725'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='technology',
            options={'ordering': ['display_order']},
        ),
        migrations.AddField(
            model_name='technology',
            name='display_order',
            field=models.IntegerField(default=499),
        ),
    ]