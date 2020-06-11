# Generated by Django 2.2.8 on 2020-06-02 19:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0003_auto_20200503_1817'),
        ('initiative_enabler', '0011_techcollectiveinterest'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectiveRestriction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('description', models.CharField(max_length=512)),
            ],
        ),
        migrations.CreateModel(
            name='RestrictionValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=32)),
                ('restriction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='initiative_enabler.CollectiveRestriction')),
            ],
        ),
        migrations.AlterField(
            model_name='initiatedcollective',
            name='address',
            field=models.CharField(default='', max_length=128, verbose_name='Adres'),
        ),
        migrations.AlterField(
            model_name='initiatedcollective',
            name='name',
            field=models.CharField(default='', max_length=128, verbose_name='Naam'),
        ),
        migrations.AlterField(
            model_name='initiatedcollective',
            name='phone_number',
            field=models.CharField(max_length=15, verbose_name='Tel'),
        ),
        migrations.CreateModel(
            name='CollectiveQuestionRestriction',
            fields=[
                ('collectiverestriction_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='initiative_enabler.CollectiveRestriction')),
                ('regex', models.CharField(blank=True, max_length=128, null=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Questionaire.Question')),
            ],
            bases=('initiative_enabler.collectiverestriction',),
        ),
        migrations.DeleteModel(
            name='CollectiveFilter',
        ),
        migrations.AddField(
            model_name='initiatedcollective',
            name='restriction_scopes',
            field=models.ManyToManyField(to='initiative_enabler.RestrictionValue'),
        ),
        migrations.AddField(
            model_name='techcollective',
            name='restrictions',
            field=models.ManyToManyField(to='initiative_enabler.CollectiveRestriction'),
        ),
    ]
