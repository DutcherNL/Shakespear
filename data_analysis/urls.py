from django.urls import path, include

from . import views, json_charts

app_name = "data_analysis"

urlpatterns = [
    path('', views.TestView.as_view(), name='overview'),
    path('json/', include([
        path('inquiry_progress', json_charts.InquiryProgressChart.as_view(), name='json_progress'),
    ]))
]