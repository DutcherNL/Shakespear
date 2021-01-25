from django.urls import path, include

from .views import SetUpOverview

url_key = 'setup'

urlpatterns = [
    path('', SetUpOverview.as_view(), name='home'),
    path('reports/', include('reports.urls')),
    # path('mailings/', include('questionaire_mailing.urls')),
    # path('data_storage/', include('local_data_storage.urls')),
    path('queued_tasks/', include('queued_tasks.urls')),

]