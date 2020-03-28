from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotFound

from questionaire_mailing.models import MailTask
from PageDisplay.sites import PageSite


class MailSite(PageSite):
    """ A custom site for the page display """

    use_page_keys = False
    breadcrumb_trail_template = "questionaire_mailing/snippet_breadcrumb_trail_mailings.html"
    site_context_fields = ['mail_task']
    include_modules = ['TextModule', 'TitleModule']

    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ A method that sets view specific parameters, triggered in each view upon dispatch
        This methoed can also check access by raising a 404Error or 403Error
        """
        view_obj.mail_task = get_object_or_404(MailTask, id=kwargs['mail_id'])
        try:
            view_obj.page = view_obj.mail_task.layout
        except MailTask.DoesNotExist:
            raise HttpResponseNotFound("Mailtask does not exist")

    @staticmethod
    def get_url_kwargs(view_obj):
        return {
            'mail_id': view_obj.mail_task.id,
        }


mail_site = MailSite()
