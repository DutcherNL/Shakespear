from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.urls import reverse

from reports.models import ReportPage
from reports.forms import SelectPageLayoutForm
from PageDisplay.sites import PageSite
from PageDisplay.views import PageInfoView


class ReportDesignSite(PageSite):
    """ A custom site for the page display """

    use_page_keys = False
    template_engine = "Default_Template"
    breadcrumb_trail_template = "reports/page_display/snippet_report_breadcrumbs.html"
    site_context_fields = ['report_page']

    can_be_deleted = True

    extra_page_options = {
        'layout_settings': {
            'button': {
                'type': 'btn-info',
                'text': mark_safe('<i class="fas fa-palette"></i> Layout settings')
            },
            'text': "Layout settings",
            'form_class': SelectPageLayoutForm,
            'return_on_success': False,
        },
        'download_pdf': {
            'button': {
                'type': 'btn-warning',
                'url': 'setup:reports:pdf',
                'text': mark_safe('<i class="fas fa-file-download"></i> Download as pdf'),
            }
        }
    }

    def get_header_buttons(self, view_class):
        from django.urls import reverse
        buttons = super(ReportDesignSite, self).get_header_buttons(view_class)

        def reverse_url(target_page):
            if target_page is None:
                return None

            url_kwargs = {
                'report_slug': target_page.reportpagelink.report.slug,
                'report_page_id': target_page.id,
            }
            if view_class == PageInfoView:
                return reverse('setup:reports:pages:view_page', kwargs=url_kwargs)
            else:
                return reverse('setup:reports:pages:edit_page', kwargs=url_kwargs)

        def get_next_page_url(view_obj):
            target_page = ReportPage.objects. \
                filter(reportpagelink__report=view_obj.report_page.reportpagelink.report,
                       reportpagelink__page_number__gt=view_obj.report_page.reportpagelink.page_number). \
                order_by('reportpagelink__page_number').first()
            return reverse_url(target_page)

        def get_prev_page_url(view_obj):
            target_page = ReportPage.objects. \
                filter(reportpagelink__report=view_obj.report_page.reportpagelink.report,
                       reportpagelink__page_number__lt=view_obj.report_page.reportpagelink.page_number). \
                order_by('reportpagelink__page_number').last()
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
            'report_slug': view_obj.report_page.reportpagelink.report.slug,
        }

    def delete_success_url(self, page, **url_kwargs):
        return reverse('setup:reports:details', kwargs={'report_slug': url_kwargs['report_slug']})


report_site = ReportDesignSite()
