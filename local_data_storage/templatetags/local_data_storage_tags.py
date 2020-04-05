from django import template

from local_data_storage.models import DataColumn

register = template.Library()


@register.filter
def get_column_value(data_obj, data_column):
    """
    Get the total technology score
    :param technology:
    :param inquiry:
    :return:
    """
    return data_obj.__getattribute__(str(data_column.db_column_name))


@register.filter
def get_column_type_shorthand(data_column):
    if data_column.column_type == DataColumn.INTFIELD:
        return "int"
    elif data_column.column_type == DataColumn.FLOATFIELD:
        return "float"
    elif data_column.column_type == DataColumn.CHARFIELD:
        return "string"
    return "-?-"
