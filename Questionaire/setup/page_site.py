from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotFound

from Questionaire.models import Technology, PageEntryQuestion
from Questionaire.models import Page as InquiryPage
from Questionaire.modules.modules import QuestionModule
from Questionaire.renderers import *
from PageDisplay.models import Page
from PageDisplay.sites import PageSite


class TechPageSite(PageSite):
    """ A custom site for the page display """

    namespace = 'pages'
    use_page_keys = False
    breadcrumb_trail_template = "inquiry/setup/snippet_breadcrumb_trail_technologies.html"
    site_context_fields = ['technology']

    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ A method that sets view specific parameters, triggered in each view upon dispatch
        This methoed can also check access by raising a 404Error or 403Error
        """
        view_obj.technology = get_object_or_404(Technology, id=kwargs['tech_id'])
        try:
            view_obj.page = view_obj.technology.information_page
        except Page.DoesNotExist:
            raise HttpResponseNotFound("Technology does not contain an information page")

    @staticmethod
    def get_url_kwargs(view_obj):
        return {
            'tech_id': view_obj.technology.id,
        }


class InquiryPagesSite(PageSite):
    """ A custom site for the page display """

    namespace = 'inquiry_pages'
    use_page_keys = False
    renderer = InquiryPagePreviewRenderer
    breadcrumb_trail_template = "inquiry/setup/snippet_breadcrumb_trail_questionaire_pages.html"
    site_context_fields = ['inquiry_page']
    include_modules = ['TextModule', 'TitleModule', 'QuestionModule', 'DownloadFileModule',]

    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ A method that sets view specific parameters, triggered in each view upon dispatch
        This methoed can also check access by raising a 404Error or 403Error
        """
        view_obj.inquiry_page = get_object_or_404(InquiryPage, id=kwargs['page_id'])
        try:
            view_obj.page = view_obj.inquiry_page.display_page
        except Page.DoesNotExist:
            raise HttpResponseNotFound("Technology does not contain an information page")

    @staticmethod
    def get_url_kwargs(view_obj):
        return {
            'page_id': view_obj.inquiry_page.id,
        }

    def on_module_creation(self, page, module):
        """ Method called when a module is created. Can be useful for triggering other events """
        if isinstance(module, QuestionModule):
            questionaire_page = page.page_set.first()
            PageEntryQuestion.objects.create(
                question=module.question,
                page=questionaire_page
            )

    def on_module_deletion(self, page, module):
        """ Method called when a module is deleted. Can be useful for triggering other events """
        if isinstance(module, QuestionModule):
            page.page_set.first().questions.remove(module.question)


tech_page_site = TechPageSite()
inquiry_pages_site = InquiryPagesSite()