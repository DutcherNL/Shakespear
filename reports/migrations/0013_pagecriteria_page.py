# Generated by Django 3.0 on 2020-02-07 11:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0012_auto_20200207_1234'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagecriteria',
            name='page',
            field=models.ForeignKey(default=52, on_delete=django.db.models.deletion.CASCADE, to='reports.ReportPage'),
            preserve_default=False,
        ),
    ]
