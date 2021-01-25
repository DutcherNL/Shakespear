from django.urls import path, include, register_converter

from reports import views
from reports.url_converters import PageLayoutConverter


register_converter(PageLayoutConverter, 'layout')

app_name = "reports"

urlpatterns = [
    # Todo: Check if the following 3 urls are actually used, does not seem to be the case.
    path('preview/', include([
        path('', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
        path('<int:page_number>/', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
    ])),
    path('plot/', views.ResultsPDFPlotter.as_view(), name='results_pdf'),
]