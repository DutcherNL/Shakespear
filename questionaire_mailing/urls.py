from django.urls import path, include

from .mail_site import mail_site
from . import views

app_name = 'mailings'

urlpatterns = [
    path('', views.MailSetupOverview.as_view(), name='overview'),
    path('add_timed/', views.AddTimedMailView.as_view(), name='add_timed'),
    path('<int:mail_id>/', include([
        path('page/', mail_site.urls),
        path('options/', views.UpdateMailTaskView.as_view(), name='update'),
        path('activate/', views.ActivateMailTaskView.as_view(), name='activate'),
        path('deactivate/', views.DeactivateMailTaskView.as_view(), name='deactivate'),
        ])),


]