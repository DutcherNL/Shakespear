# Generated by Django 3.0 on 2020-03-23 17:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('PageDisplay', '0012_whitespacemodule'),
        ('questionaire_mailing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MailPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='PageDisplay.Page')),
            ],
            bases=('PageDisplay.page',),
        ),
        migrations.AddField(
            model_name='timedmailtask',
            name='trigger',
            field=models.CharField(choices=[('TC', 'After completion'), ('TI', 'After creation (incomplete)'), ('LC', 'After Last Login (Completed)'), ('LI', 'After Last Login (Incomplete)')], default='TC', max_length=2),
            preserve_default=False,
        ),
    ]
