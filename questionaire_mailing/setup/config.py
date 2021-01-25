from django.urls import path, include


from shakespeare_setup.config import SetupConfig
from questionaire_mailing.setup import views
from .mail_site import mail_site


class SetupMails(SetupConfig):
    name = "Timed mailing"
    url_keyword = 'mailing'
    namespace = 'mailings'
    root_url_name = 'overview'
    access_required_permissions = ['questionaire_mailing.change_mailtask']

    button = {
        'image': 'img/questionaire_mailing/setup/timed-mail.svg'
    }

    def get_urls(self):
        """ Builds a list of urls """
        return [
            path('', views.MailSetupOverview.as_view(), name='overview'),
            path('add_timed/', views.AddTimedMailView.as_view(), name='add_timed'),
            path('add_triggered/', views.AddTriggeredMailView.as_view(), name='add_triggered'),
            path('<int:mail_id>/', include([
                path('page/', mail_site.urls),
                path('options/', views.UpdateMailTaskView.as_view(), name='update'),
                path('activate/', views.ActivateMailTaskView.as_view(), name='activate'),
                path('deactivate/', views.DeactivateMailTaskView.as_view(), name='deactivate'),
            ])),
        ]