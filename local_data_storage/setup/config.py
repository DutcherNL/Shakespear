from django.urls import path, include


from shakespeare_setup.config import SetupConfig
from . import views


class SetupTechs(SetupConfig):
    name = "Local data storage"
    url_keyword = 'data-storage'
    namespace = 'local_data_storage'
    root_url_name = 'data_domain_overview'
    access_required_permissions = ['local_data_storage.change_datatable']

    button = {
        'class': 'btn-primary',
        'image': "img/local_data_storage/local-data-storage-icon.svg",
    }

    def get_urls(self):
        """ Builds a list of urls """
        return [
            path('', views.LocalDataStorageOverview.as_view(), name='data_domain_overview'),
            path('add/', views.AddLocalDataStorageView.as_view(), name='add_local_data_domain'),
            path('<slug:table_slug>/', include([
                path('', views.DataTableDetailRedirectView.as_view(), name='data_table_info'),
                path('edit/', views.UpdateLocalDataStorageView.as_view(), name='data_table_edit'),
                path('delete/', views.DeleteLocalDataStorageView.as_view(), name='data_table_delete'),
                path('migrate/', views.MigrateView.as_view(), name='data_table_migrate'),
                path('add_column/', views.AddDataColumnView.as_view(), name='add_data_column'),
                path('column/<slug:column_slug>/', include([
                    path('edit/', views.UpdateDataColumnView.as_view(), name='edit_data_column'),
                    path('delete/', views.DeleteDataColumnView.as_view(), name='delete_data_column'),
                ])),
                path('data/', include([
                    path('add/', views.AddDataView.as_view(), name='add_data_entry'),
                    path('add_csv/', views.AddCSVDataView.as_view(), name='add_data_entries_csv'),
                    path('<int:data_id>/', include([
                        path('edit/', views.UpdateDataView.as_view(), name='update_data_entry'),
                        path('delete/', views.DeleteDataView.as_view(), name='delete_data_entry'),
                    ]))
                ]))
            ])),
        ]