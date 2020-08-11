from django.urls import path, include
from django.views.generic import RedirectView

from inquirer_settings import views

app_name = "inquirer_settings"

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='inquirer_settings:home', permanent=False)),
    path('settings/', include([
        path('', views.InquirerSettingsHome.as_view(), name='home'),
        path('mail/', include([
            path('', views.InquirerMailSettingsView.as_view(), name='mail'),
            path('resend/', views.ReSendMailValidationView.as_view(), name='resend_validation_mail'),
        ])),

        path('interests/', views.CollectiveInterestView.as_view(), name='tech_cols'),
        path('verzamelde_gegevens/', views.InquirerAnswersView.as_view(), name='answers'),
    ])),
    path('validate_mail/', include([
        path('', views.EmailValidationView.as_view(), name='validate_mail'),
        path('success/', views.EmailValidationSuccessView.as_view(), name='validate_mail_success'),
    ])),
]