# Generated by Django 2.2.8 on 2020-07-10 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('initiative_enabler', '0016_auto_20200624_1126'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiveapprovalresponse',
            name='address',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]