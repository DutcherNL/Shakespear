# Generated by Django 2.2.8 on 2020-05-18 13:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('initiative_enabler', '0008_auto_20200513_1649'),
    ]

    operations = [
        migrations.RenameField(
            model_name='initiatedcollective',
            old_name='host_address',
            new_name='address',
        ),
        migrations.AlterField(
            model_name='techcollective',
            name='technology',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='Questionaire.Technology'),
        ),
    ]
