# Generated by Django 2.1.5 on 2019-04-22 13:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Questionaire', '0010_answeroption_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='inquiryquestionanswer',
            name='processed_answer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Questionaire.AnswerOption'),
        ),
    ]