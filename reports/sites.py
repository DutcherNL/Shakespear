from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotFound

from reports.models import ReportPage
from PageDisplay.models import Page
from PageDisplay.sites import PageSite


class ReportDesignSite(PageSite):
    """ A custom site for the page display """

    use_page_keys = False

    def get_header_buttons(self, view_class):
        from django.urls import reverse
        buttons = super(ReportDesignSite, self).get_header_buttons(view_class)

        def create_report_page_url(view_obj):
            print(f"Test A {view_obj}")
            url_kwargs = {
                'report_slug': view_obj.report_page.report.slug,
                'report_page_id': view_obj.report_page.id,
            }
            return reverse('setup:reports:details', kwargs=url_kwargs)

        buttons['Report Page Details'] = create_report_page_url
        return buttons

    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ A method that sets view specific parameters, triggered in each view upon dispatch
        This methoed can also check access by raising a 404Error or 403Error
        """
        view_obj.report_page = get_object_or_404(ReportPage, id=kwargs['report_page_id'])
        try:
            view_obj.page = view_obj.report_page.display_page
        except Page.DoesNotExist:
            raise HttpResponseNotFound("ReportPage does not contain a displayable page")

    @staticmethod
    def get_url_kwargs(view_obj):
        return {
            'report_page_id': view_obj.report_page.id,
            'report_slug': view_obj.report_page.report.slug,
        }


report_site = ReportDesignSite()
