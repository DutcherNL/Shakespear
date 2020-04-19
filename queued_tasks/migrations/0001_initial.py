# Generated by Django 3.0 on 2020-04-11 21:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('local_data_storage', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QueuedTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_on', models.DateTimeField(auto_created=True)),
                ('state', models.IntegerField(choices=[(2, 'Freshman'), (1, 'Sophomore'), (0, 'Junior'), (-1, 'Failed')])),
                ('completed_on', models.DateTimeField(blank=True, null=True)),
                ('progress', models.PositiveIntegerField(blank=True, default=None, null=True)),
                ('feedback', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='QueuedCSVDataProcessingTask',
            fields=[
                ('queuedtask_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='queued_tasks.QueuedTask')),
                ('csv_file', models.FileField(blank=True, null=True, upload_to='')),
                ('overwrite_with_empty', models.BooleanField(default=False)),
                ('deliminator', models.CharField(default=';', max_length=1)),
                ('data_table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='local_data_storage.DataTable')),
            ],
            bases=('queued_tasks.queuedtask',),
        ),
    ]