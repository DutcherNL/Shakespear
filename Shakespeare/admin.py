from django.contrib.admin import AdminSite
from django.conf import settings


class MyAdminSite(AdminSite):
    """Custom admin site. See
    https://docs.djangoproject.com/en/2.1/ref/contrib/admin/#overriding-the-default-admin-site."""
    site_header = f"{settings.SITE_DISPLAY_NAME} administration"
    site_title = f"{settings.SITE_DISPLAY_NAME}"
