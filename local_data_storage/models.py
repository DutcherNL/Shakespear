from django.db import models
from django.shortcuts import reverse
from django.core.exceptions import ValidationError
from django.utils.text import slugify
import re

from local_data_storage.migration_management import migrate_to_database, destroy_table_on_db, get_as_db_name


class DataTable(models.Model):
    """ Contains an overall code declaration """
    name = models.CharField(max_length=32, unique=True)
    slug = models.SlugField()
    description = models.CharField(max_length=255)

    key_column_name = models.CharField(max_length=32, default="key", verbose_name="Name of the key column")
    key_regex = models.CharField(max_length=255, null=True, blank=True, verbose_name="Regex code for the key entries")

    _db_key_column_name = models.CharField(max_length=150, blank=True, null=True)
    _db_table_class_name = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=False)

    @property
    def db_key_column_name(self):
        if self.is_active:
            return self._db_key_column_name
        else:
            return get_as_db_name(self.key_column_name)

    @property
    def db_table_class_name(self):
        if self.is_active:
            return self._db_table_class_name
        else:
            return get_as_db_name(self.name)

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
        migrate_to_database(self.get_data_class())

        # Store all current names for the datacolumns in case the names of the visual are changed
        for column in self.datacolumn_set.all():
            column._db_column_name = column.db_column_name
            column.save()

        # Store all db related names in case the visual data is changed
        self._db_table_class_name = self.db_table_class_name
        self._db_key_column_name = self.db_key_column_name

        # Set the datatable as active
        self.is_active = True
        self.save()

    def destroy_table_on_db(self):
        if not self.is_active:
            raise RuntimeError("The datatable is not active, thus there is no database table to destroy")
        destroy_table_on_db(self.get_data_class())
        self.is_active = False
        self._db_table_class_name = None
        self._db_key_column_name = None
        self.save()

        for column in self.datacolumn_set.all():
            column._db_column_name = None
            column.save()

    def get_absolute_url(self):
        return reverse('setup:local_data_storage:data_table_info', kwargs={'table_slug': self.slug})

    def __str__(self):
        return self.name

    def get_data_table_entries(self):
        if not self.is_active:
            return None
        else:
            DataModel = DataContent.get_class_for_table(self)
            return DataModel.objects.all()

    def get_data_class(self):
        return DataContent.get_class_for_table(self)


class DataColumn(models.Model):
    """ Content identified with a given code in accordance to the code declaration """
    table = models.ForeignKey(DataTable, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    slug = models.SlugField()
    _db_column_name = models.CharField(max_length=50, null=True)

    CHARFIELD = 'CH'
    INTFIELD = 'IN'
    FLOATFIELD = 'FL'
    YEAR_IN_SCHOOL_CHOICES = [
        (CHARFIELD, 'Text field'),
        (INTFIELD, 'Integer field'),
        (FLOATFIELD, 'Float field'),
    ]
    column_type = models.CharField(max_length=2, choices=YEAR_IN_SCHOOL_CHOICES, default=CHARFIELD)

    @property
    def db_column_name(self):
        if self.table.is_active:
            return self._db_column_name
        else:
            return get_as_db_name(self.name)

    def save(self, **kwargs):
        self.slug = slugify(self.name)
        return super(DataColumn, self).save(**kwargs)

    def get_model_field(self):
        if self.column_type == self.CHARFIELD:
            return models.CharField(max_length=128, verbose_name=self.name, blank=True, null=True)
        elif self.column_type == self.INTFIELD:
            return models.IntegerField(verbose_name=self.name, blank=True, null=True)
        elif self.column_type == self.FLOATFIELD:
            return models.FloatField(verbose_name=self.name, blank=True, null=True)


class DataContent(models.Model):
    """ This class will be mixed in the actual content classes during runtime"""

    class Meta:
        abstract = True

    @property
    def get_key(self):
        return self.__getattribute__(str(self._key_name))

    def clean(self):
        # Validate that the given code adheres the regex structure
        regex = self.data_table_obj.key_regex
        if regex:
            regex_match = re.match(regex, self.__getattribute__(self._key_name))
            if regex_match is None:
                raise ValidationError("{code} does not match the required regex: {regex}".format(
                    code=self.__getattribute__(self._key_name), regex=regex
                ))

    @classmethod
    def get_class_for_table(cls, data_table_obj):
        attrs = {
            '__module__': 'local_data_storage',
        }
        cls.init_model_fields(data_table_obj, attrs)

        return type(data_table_obj.db_table_class_name, (DataContent, ), attrs)

    @classmethod
    def init_model_fields(cls, data_table_obj, attrs):
        attrs['data_table_obj'] = data_table_obj

        # Set the model key field
        attrs['_key_name'] = data_table_obj.db_key_column_name
        attrs[data_table_obj.db_key_column_name] = models.CharField(max_length=128, unique=True,
                                                                    verbose_name=data_table_obj.key_column_name)
        # Set the other property fields
        for column in data_table_obj.datacolumn_set.all():
            attrs[column.db_column_name] = column.get_model_field()



