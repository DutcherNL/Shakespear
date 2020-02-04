# Generated by Django 3.0 on 2020-02-04 14:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_auto_20200203_2221'),
    ]

    operations = [
        migrations.AddField(
            model_name='a4_pagecontainer',
            name='orientation',
            field=models.BooleanField(choices=[(True, 'Standing'), (False, 'Rotated')], default=True),
        ),
        migrations.AddField(
            model_name='a4_pagecontainer',
            name='size',
            field=models.CharField(choices=[('A3', 'A3 (297 x 420mm)'), ('A4', 'A4 (210 x 297mm)'), ('A5', 'A5 (148 x 210mm)')], default='A4', max_length=3),
        ),
    ]
