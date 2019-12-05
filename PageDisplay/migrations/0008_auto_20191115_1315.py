# Generated by Django 2.1.5 on 2019-11-15 12:15

from django.db import migrations, models
import django.db.models.deletion


def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Information = apps.get_model("PageDisplay", "Information")
    ModuleContainer = apps.get_model("PageDisplay", "ModuleContainer")
    db_alias = schema_editor.connection.alias
    for information in Information.objects.using(db_alias).all():
        container = ModuleContainer.objects.using(db_alias).create(id=information.id)
        information.modulecontainer_ptr = container
        information.save()


def reverse_func(apps, schema_editor):
    # Do nothing, not necessary
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('PageDisplay', '0007_auto_20191115_1150'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModuleContainer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AddField(
            model_name='information',
            name='modulecontainer_ptr',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='PageDisplay.ModuleContainer'),
        ),
        migrations.RunPython(forwards_func, reverse_func, atomic=False),
        migrations.RemoveField(
            model_name='information',
            name='id',
        ),
        migrations.AlterField(
            model_name='information',
            name='modulecontainer_ptr',
            field=models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='PageDisplay.ModuleContainer'),
        ),
        migrations.AlterField(
            model_name='basemodule',
            name='information',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='PageDisplay.ModuleContainer'),
        ),
    ]
