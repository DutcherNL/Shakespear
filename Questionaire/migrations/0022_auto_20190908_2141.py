# Generated by Django 2.2 on 2019-09-08 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0021_remove_technology_long_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='help_text',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
    ]