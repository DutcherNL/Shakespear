# Generated by Django 2.1.5 on 2019-06-04 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0007_auto_20190604_1249'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scoringdeclaration',
            name='slug',
        ),
        migrations.AddField(
            model_name='scoringdeclaration',
            name='display_name',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='scoringdeclaration',
            name='name',
            field=models.SlugField(max_length=32),
        ),
    ]
