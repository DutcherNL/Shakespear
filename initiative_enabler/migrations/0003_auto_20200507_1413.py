# Generated by Django 3.0 on 2020-05-07 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('initiative_enabler', '0002_auto_20200507_1301'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectiveapprovalresponse',
            name='message',
            field=models.TextField(blank=True, max_length=1200, null=True),
        ),
    ]
