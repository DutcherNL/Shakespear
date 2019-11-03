from django.urls import path, include

from reports import views

urlpatterns = [
    path('preview/', include([
        path('', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
        path('<int:page_number>/', views.QuestionaireCompletePDFView.as_view(), name='result_preview'),
    ])),
    path('plot/', views.ResultsPDFPlotter.as_view(), name='results_pdf'),
]