from django.urls import path, include

from . import views

app_name = 'queued_tasks'

urlpatterns = [
    path('', views.QueuedTaskListView.as_view(), name='overview'),
]