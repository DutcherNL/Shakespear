# Generated by Django 2.1.5 on 2019-09-07 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0018_answeroption_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='help_text',
            field=models.CharField(default='', max_length=255),
        ),
    ]