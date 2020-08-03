from django.conf import settings


def get_setting_value(attr_name, default_value):
    if hasattr(settings, 'attr_name'):
        return settings.MIN_INQUIRY_REQ
    else:
        return default_value


# Call the settings here so that it will override any basic parameter if neccessary


MIN_INQUIRY_REQ = get_setting_value('MIN_INQUIRY_REQ', 10)