from django.urls import path, include

from local_data_storage import views

app_name = "local_data_storage"

urlpatterns = [
    path('', include([
        path('', views.LocalDataStorageOverview.as_view(), name='data_domain_overview'),
        path('add/', views.AddLocalDataStorageView.as_view(), name='add_local_data_domain'),
        path('<slug:table_slug>/', include([
            path('', views.DataTableDetailView.as_view(), name='data_table_info'),
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
                path('add_csv/', views.AddDataView.as_view(), name='add_data_entries_csv'),
                path('<int:data_id>/', include([
                    path('edit/', views.UpdateDataView.as_view(), name='update_data_entry'),
                    path('delete/', views.DeleteDataView.as_view(), name='delete_data_entry'),
                ]))
            ]))
        ])),
    ])),
]