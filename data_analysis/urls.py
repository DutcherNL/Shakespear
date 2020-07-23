from django.urls import path, include

from . import views, json_charts

app_name = "data_analysis"

urlpatterns = [
    path('', views.InquiryDataView.as_view(), name='overview'),
    path('technologies/', views.TechDataView.as_view(), name='techs'),
    path('json/', include([
        path('inquiry_creation/', json_charts.InquiryCreationChart.as_view(), name='json_creation'),
        path('inquiry_progress/', json_charts.InquiryProgressChart.as_view(), name='json_progress'),
        path('tech_result/<int:tech_id>/', json_charts.TechProgressChart.as_view(), name='json_techs'),
    ]))
]