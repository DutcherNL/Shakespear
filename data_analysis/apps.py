from django.apps import AppConfig
from general.apps import PermissionUpdatingMixin


class DataAnalysisConfig(PermissionUpdatingMixin, AppConfig):
    name = 'data_analysis'
    permissions = [('can_access_data_analysis_pages', 'Can access data analysis pages'),
                   ('can_access_entry_analysis', 'Can access direct entry analysis'),]
