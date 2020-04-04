from django.db import models
from django.shortcuts import reverse
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import re

from local_data_storage.migration_management import migrate_to_database, destroy_table_on_db, get_data_model


class DataTable(models.Model):
    """ Contains an overall code declaration """
    name = models.CharField(max_length=32)
    slug = models.SlugField(editable=False)
    description = models.CharField(max_length=255)

    is_active = models.BooleanField(default=False)

    def save(self, **kwargs):
        if self.is_active:
            # Check if the state on the database is not active, otherwise it can not be saved
            db_obj = DataTable.objects.get(id=self.id)
            if db_obj.is_active:
                raise ValidationError(f"DataTable object '{self.name}' can not be saved as it is already active")

        self.slug = slugify(self.name)
        return super(DataTable, self).save(**kwargs)

    def create_table_on_db(self):
        if self.is_active:
            raise RuntimeError("The datatable is already set as active, thus the datatable should be present in the"
                               "database. You can not copy this local")
        migrate_to_database(self)
        self.is_active = True
        self.save()

    def destroy_table_on_db(self):
        if not self.is_active:
            raise RuntimeError("The datatable is not active, thus there is no database table to destroy")
        destroy_table_on_db(self)
        self.is_active = False
        self.save()

    def get_absolute_url(self):
        return reverse('setup:local_data_storage:data_table_info', kwargs={'table_slug': self.slug})

    def __str__(self):
        return self.name

    def get_data_table_entries(self):
        if not self.is_active:
            return None
        else:
            DataModel = get_data_model(self)
            return DataModel.objects.all()

    def get_data_class(self):
        return get_data_model(self)


class DataColumn(models.Model):
    """ Content identified with a given code in accordance to the code declaration """
    table = models.ForeignKey(DataTable, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    slug = models.SlugField()

    def save(self, **kwargs):
        self.slug = slugify(self.name)
        return super(DataColumn, self).save(**kwargs)




