from django.urls import path

from .views import DataLookupView

urlpatterns = [
    path('', DataLookupView.as_view(), name='DataView'),
]