# Generated by Django 2.2.8 on 2020-07-06 01:11

import PageDisplay.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('PageDisplay', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DownloadFileModule',
            fields=[
                ('basemodule_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='PageDisplay.BaseModule')),
                ('file', models.FileField(blank=True, null=True, upload_to='')),
                ('description', models.CharField(max_length=512)),
            ],
            bases=(PageDisplay.models.BasicModuleMixin, 'PageDisplay.basemodule'),
        ),
    ]