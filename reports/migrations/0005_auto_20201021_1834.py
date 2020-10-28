# Generated by Django 2.2.8 on 2020-10-21 16:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_reportpage_layout'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagelayout',
            name='description',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='pagelayout',
            name='name',
            field=models.CharField(default='first_layout', max_length=64),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pagelayout',
            name='slug',
            field=models.SlugField(blank=True, editable=False, max_length=128, unique=True),
        ),
    ]