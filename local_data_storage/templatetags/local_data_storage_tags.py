from django import template

register = template.Library()


@register.filter
def get_attribute(data_obj, attribute):
    """
    Get the total technology score
    :param technology:
    :param inquiry:
    :return:
    """
    return data_obj.__getattribute__(str(attribute))