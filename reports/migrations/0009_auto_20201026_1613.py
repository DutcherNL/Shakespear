# Generated by Django 2.2.8 on 2020-10-26 15:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_transer_link_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reportpage',
            name='last_edited_old',
        ),
        migrations.RemoveField(
            model_name='reportpage',
            name='page_number',
        ),
        migrations.RemoveField(
            model_name='reportpage',
            name='report',
        ),
        migrations.AlterField(
            model_name='reportpagelink',
            name='page',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='reports.ReportPage'),
        ),
    ]