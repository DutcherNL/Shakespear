# Generated by Django 2.1.5 on 2019-03-11 21:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('position', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='PageEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=999)),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Questionaire.Page')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Questionaire.Question')),
            ],
        ),
        migrations.DeleteModel(
            name='Questionpage',
        ),
        migrations.AddField(
            model_name='page',
            name='questions',
            field=models.ManyToManyField(through='Questionaire.PageEntry', to='Questionaire.Question'),
        ),
    ]
