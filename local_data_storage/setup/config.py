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
        wrap = self.limit_access
        return [
            path('', wrap(views.LocalDataStorageOverview.as_view()), name='data_domain_overview'),
            path('add/', wrap(views.AddLocalDataStorageView.as_view()), name='add_local_data_domain'),
            path('<slug:table_slug>/', include([
                path('', wrap(views.DataTableDetailRedirectView.as_view()), name='data_table_info'),
                path('edit/', wrap(views.UpdateLocalDataStorageView.as_view()), name='data_table_edit'),
                path('delete/', wrap(views.DeleteLocalDataStorageView.as_view()), name='data_table_delete'),
                path('migrate/', wrap(views.MigrateView.as_view()), name='data_table_migrate'),
                path('add_column/', wrap(views.AddDataColumnView.as_view()), name='add_data_column'),
                path('column/<slug:column_slug>/', include([
                    path('edit/', wrap(views.UpdateDataColumnView.as_view()), name='edit_data_column'),
                    path('delete/', wrap(views.DeleteDataColumnView.as_view()), name='delete_data_column'),
                ])),
                path('data/', include([
                    path('add/', wrap(views.AddDataView.as_view()), name='add_data_entry'),
                    path('add_csv/', wrap(views.AddCSVDataView.as_view()), name='add_data_entries_csv'),
                    path('<int:data_id>/', include([
                        path('edit/', wrap(views.UpdateDataView.as_view()), name='update_data_entry'),
                        path('delete/', wrap(views.DeleteDataView.as_view()), name='delete_data_entry'),
                    ]))
                ]))
            ])),
        ]