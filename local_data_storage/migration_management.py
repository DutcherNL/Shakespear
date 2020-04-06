from django.db import models, connection
from django.utils.text import slugify


def get_as_db_name(name):
    name = slugify(name, allow_unicode=False)
    return name.replace('-', '_')


def get_data_model(data_table_obj):
    model_fields = {
        '__module__': 'local_data_storage'
    }

    for column in data_table_obj.datacolumn_set.all():
        model_fields[column.slug] = models.CharField(max_length=128, null=True)

    return type(data_table_obj.slug, (models.Model, ), model_fields)


def migrate_to_database(DataModel):
    """ Creates a database table corresponding with the DataTable object """
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(DataModel)


def destroy_table_on_db(DataModel):
    with connection.schema_editor() as schema_editor:
        schema_editor.delete_model(DataModel)











