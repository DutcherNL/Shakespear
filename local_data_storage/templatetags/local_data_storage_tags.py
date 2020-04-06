from django import template
from widget_tweaks.templatetags.widget_tweaks import FieldAttributeNode

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


@register.simple_tag()
def render_filter_field(form, column=None, **kwargs):
    if column is not None:
        for field in form.visible_fields():
            if form.get_as_field_name(column.db_column_name) == field.name:
                return field.as_widget(attrs=kwargs)
    else:
        for field in form.visible_fields():
            if form.key_field_name == field.name:
                return field.as_widget(attrs=kwargs)
    return ""

# FieldAttributeNode(field, [('class', 'form-control')], [])
#{% render_field field class="form-control" placeholder=field.label %}
