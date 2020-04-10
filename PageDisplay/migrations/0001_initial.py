# Generated by Django 3.0 on 2020-04-07 12:50

import PageDisplay.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseModule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_type', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ImageModule',
            fields=[
                ('basemodule_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='PageDisplay.BaseModule')),
                ('image', models.ImageField(upload_to='')),
                ('caption', models.CharField(blank=True, default='', max_length=256, null=True)),
                ('height', models.PositiveIntegerField(default=100)),
                ('mode', models.SlugField(choices=[('auto', 'Display full image'), ('full', 'Cover image')], default='auto')),
                ('css', models.CharField(blank=True, default='', help_text='CSS classes in accordance with Bootstrap', max_length=256, null=True)),
            ],
            bases=(PageDisplay.models.BasicModuleMixin, 'PageDisplay.basemodule'),
        ),
        migrations.CreateModel(
            name='TextModule',
            fields=[
                ('basemodule_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='PageDisplay.BaseModule')),
                ('text', models.TextField()),
                ('css', models.CharField(blank=True, default='', help_text='CSS classes in accordance with Bootstrap', max_length=256, null=True)),
            ],
            bases=(PageDisplay.models.BasicModuleMixin, 'PageDisplay.basemodule'),
        ),
        migrations.CreateModel(
            name='TitleModule',
            fields=[
                ('basemodule_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='PageDisplay.BaseModule')),
                ('title', models.CharField(max_length=127)),
                ('size', models.PositiveIntegerField(default=1, help_text='The level of the title 1,2,3... maz 5')),
                ('css', models.CharField(blank=True, default='', help_text='CSS classes in accordance with Bootstrap', max_length=256, null=True)),
            ],
            bases=(PageDisplay.models.BasicModuleMixin, 'PageDisplay.basemodule'),
        ),
        migrations.CreateModel(
            name='WhiteSpaceModule',
            fields=[
                ('basemodule_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='PageDisplay.BaseModule')),
                ('height', models.PositiveIntegerField(default=100, validators=[django.core.validators.MinValueValidator(limit_value=25), django.core.validators.MaxValueValidator(limit_value=1000)])),
            ],
            bases=(PageDisplay.models.BasicModuleMixin, 'PageDisplay.basemodule'),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=63)),
                ('root_module', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='PageDisplay.BaseModule')),
            ],
        ),
        migrations.CreateModel(
            name='ContainerModulePositionalLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=999)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='container_link', to='PageDisplay.BaseModule')),
            ],
            options={
                'ordering': ['-position'],
            },
        ),
        migrations.CreateModel(
            name='OrderedContainerModule',
            fields=[
                ('basemodule_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='PageDisplay.BaseModule')),
                ('module_list', models.ManyToManyField(related_name='container', through='PageDisplay.ContainerModulePositionalLink', to='PageDisplay.BaseModule')),
            ],
            bases=(PageDisplay.models.ContainerModuleMixin, 'PageDisplay.basemodule'),
        ),
        migrations.CreateModel(
            name='VerticalContainerModule',
            fields=[
                ('orderedcontainermodule_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='PageDisplay.OrderedContainerModule')),
            ],
            bases=('PageDisplay.orderedcontainermodule',),
        ),
        migrations.AddField(
            model_name='containermodulepositionallink',
            name='container',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='module_link', to='PageDisplay.OrderedContainerModule'),
        ),
    ]
