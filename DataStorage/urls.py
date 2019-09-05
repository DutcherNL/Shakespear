from django.urls import path

from .views import DataLookupView, DataUploadFromCSVView

urlpatterns = [
    path('', DataLookupView.as_view(), name='DataView'),
    path('add/', DataUploadFromCSVView.as_view(), name='CSVView'),
]