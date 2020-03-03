from django.shortcuts import get_object_or_404

from reports.models import ReportPage
from PageDisplay.sites import PageSite
from PageDisplay.views import PageInfoView


class ReportDesignSite(PageSite):
    """ A custom site for the page display """

    use_page_keys = False
    template_engine = "Default_Template"
    breadcrumb_trail_template = "reports/page_display/snippet_report_breadcrumbs.html"
    site_context_fields = ['report_page']

    def get_header_buttons(self, view_class):
        from django.urls import reverse
        buttons = super(ReportDesignSite, self).get_header_buttons(view_class)

        def reverse_url(target_page):
            if target_page is None:
                return None

            url_kwargs = {
                'report_slug': target_page.report.slug,
                'report_page_id': target_page.id,
            }
            if view_class == PageInfoView:
                return reverse('setup:reports:pages:view_page', kwargs=url_kwargs)
            else:
                return reverse('setup:reports:pages:edit_page', kwargs=url_kwargs)

        def get_next_page_url(view_obj):
            target_page = ReportPage.objects. \
                filter(report=view_obj.report_page.report,
                       page_number__gt=view_obj.report_page.page_number). \
                order_by('page_number').first()
            return reverse_url(target_page)

        def get_prev_page_url(view_obj):
            target_page = ReportPage.objects. \
                filter(report=view_obj.report_page.report,
                       page_number__lt=view_obj.report_page.page_number). \
                order_by('page_number').last()
            return reverse_url(target_page)

        buttons['Next page'] = get_next_page_url
        buttons['Previous page'] = get_prev_page_url
        buttons['Previous page'].get_next = False
        return buttons

    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ A method that sets view specific parameters, triggered in each view upon dispatch
        This methoed can also check access by raising a 404Error or 403Error
        """
        view_obj.report_page = get_object_or_404(ReportPage, id=kwargs['report_page_id'])
        view_obj.page = view_obj.report_page

    @staticmethod
    def get_url_kwargs(view_obj):
        return {
            'report_page_id': view_obj.report_page.id,
            'report_slug': view_obj.report_page.report.slug,
        }


report_site = ReportDesignSite()
