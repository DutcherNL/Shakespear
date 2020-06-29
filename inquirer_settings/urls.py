from django.urls import path, include

from inquirer_settings import views

app_name = "inquirer_settings"

urlpatterns = [
    path('settings/', include([
        path('home/', views.InquirerSettingsHome.as_view(), name='home'),
        path('mail/', views.InquirerMailSettingsView.as_view(), name='mail'),
        path('interests/', views.CollectiveInterestView.as_view(), name='tech_cols'),
        path('verzamelde_gegevens/', views.InquirerAnswersView.as_view(), name='answers'),
    ])),
]