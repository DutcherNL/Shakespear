# Generated by Django 2.2.8 on 2020-07-13 16:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('initiative_enabler', '0017_auto_20200710_1543'),
    ]

    operations = [
        migrations.CreateModel(
            name='RestrictionRangeAdjustment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min', models.IntegerField(default=1000)),
                ('range', models.IntegerField(default=1)),
                ('max', models.IntegerField(default=9999)),
            ],
        ),
        migrations.RemoveField(
            model_name='techcollective',
            name='restrictions',
        ),
        migrations.AlterField(
            model_name='initiatedcollective',
            name='message',
            field=models.TextField(max_length=500, verbose_name='Uitnodigings bericht'),
        ),
        migrations.AlterField(
            model_name='initiatedcollective',
            name='phone_number',
            field=models.CharField(max_length=15, verbose_name='Telefoonnummer'),
        ),
        migrations.CreateModel(
            name='RestrictionLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collective', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='initiative_enabler.TechCollective')),
                ('range_adjustment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='initiative_enabler.RestrictionRangeAdjustment')),
                ('restriction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='initiative_enabler.CollectiveRestriction')),
            ],
        ),
    ]
