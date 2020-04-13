from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class ShakespeareGeneralConfig(AppConfig):
    name = 'general'


class MyAdminConfig(AdminConfig):
    default_site = 'Shakespeare.admin.MyAdminSite'
