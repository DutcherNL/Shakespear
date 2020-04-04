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
            path('<slug:column_slug>/', include([
                path('edit/', views.UpdateDataColumnView.as_view(), name='edit_data_column'),
                path('delete/', views.DeleteDataColumnView.as_view(), name='delete_data_column'),
            ]))
        ])),
    ])),
]