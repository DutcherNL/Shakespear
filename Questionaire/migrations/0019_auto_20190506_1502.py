# Generated by Django 2.1.5 on 2019-05-06 13:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0018_auto_20190506_1426'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageRequirementStoredValue',
            fields=[
                ('pagerequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='Questionaire.PageRequirement')),
                ('value_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Questionaire.StoredValueDeclaration')),
            ],
            bases=('Questionaire.pagerequirement',),
        ),
        migrations.CreateModel(
            name='PageRequirementTechImportance',
            fields=[
                ('pagerequirement_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='Questionaire.PageRequirement')),
                ('technology', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Questionaire.Technology')),
            ],
            bases=('Questionaire.pagerequirement',),
        ),
        migrations.RenameModel(
            old_name='AnswerScoring',
            new_name='AnswerScoringTechnology',
        ),
        migrations.AddField(
            model_name='storedinquiryvalue',
            name='inquiry',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='Questionaire.Inquiry'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='storedinquiryvalue',
            name='value_info',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='Questionaire.StoredValueDeclaration'),
            preserve_default=False,
        ),
    ]
