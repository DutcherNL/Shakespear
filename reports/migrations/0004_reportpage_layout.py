# Generated by Django 2.2.8 on 2020-10-20 15:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_pagelayout'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportpage',
            name='layout',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='reports.PageLayout'),
        ),
    ]
