# Generated by Django 2.2.8 on 2021-05-19 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('initiative_enabler', '0026_auto_20210519_1458'),
    ]

    operations = [
        migrations.AlterField(
            model_name='techcollectiveinterest',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
