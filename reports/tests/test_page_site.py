from django.test import TestCase
from django.urls import reverse

from general.tests.mixins.test_view_mixins import *

from PageDisplay.sites import PageSite
from PageDisplay.views import PageInfoView
from reports.models import *
from reports.setup.sites import report_site
from reports.forms import SelectPageLayoutForm


class TestReportSite(TestCase):
    fixtures = ['test_report.json']

    def test_class(self):
        rs_class = report_site.__class__
        self.assertTrue(issubclass(rs_class, PageSite))
        self.assertFalse(rs_class.use_page_keys)
        self.assertEqual(rs_class.template_engine, 'Default_Template')
        self.assertIn('report_page', rs_class.site_context_fields)

        self.assertTrue(rs_class.can_be_deleted)

    def test_extra_page_options(self):
        assertEqualInMultidict(
            report_site.extra_page_options,
            'layout_settings.form_class',
            SelectPageLayoutForm,
        )
        assertEqualInMultidict(
            report_site.extra_page_options,
            'layout_settings.return_on_success',
            False,
        )
        assertEqualInMultidict(
            report_site.extra_page_options,
            'criterias.button.url',
            'setup:reports:page_criterias',
        )
        assertEqualInMultidict(
            report_site.extra_page_options,
            'download_pdf.button.url',
            'setup:reports:pdf',
        )

    def test_buttons_edit(self):
        # Just take an ordinary view, the buttons should be there on any class
        class TestView:
            report_page = ReportPage.objects.get(id=4)
        buttons = report_site.get_header_buttons(view_class=TestView)

        # Tests if buttons are present, are methods and return the correct url
        self.assertIn('Next page', buttons)
        self.assertTrue(callable(buttons['Next page']), msg="Next page button content was not a function")
        # Test the url the method should return
        self.assertEqual(
            buttons['Next page'](TestView()),
            reverse(
                'setup:reports:pages:edit_page',
                kwargs={
                    'report_slug': 'test-basic-report',
                    'report_page_id': 3,
                })
        )

        self.assertIn('Previous page', buttons)
        self.assertTrue(callable(buttons['Previous page']), msg="Previous page button content was not a function")
        self.assertEqual(
            buttons['Next page'](TestView()),
            reverse(
                'setup:reports:pages:edit_page',
                kwargs={
                    'report_slug': 'test-basic-report',
                    'report_page_id': 3,
                })
        )

    def test_buttons_view(self):
        # Just take an ordinary view, the buttons should be there on any class
        buttons = report_site.get_header_buttons(view_class=PageInfoView)

        # Test that it returns a view_page instead when in the PageInfoView class
        view_obj = PageInfoView()
        view_obj.report_page = ReportPage.objects.get(id=4)
        self.assertIn('Previous page', buttons)
        self.assertTrue(callable(buttons['Previous page']), msg="Next page button content was not a function")
        self.assertEqual(
            buttons['Next page'](view_obj),
            reverse(
                'setup:reports:pages:view_page',
                kwargs={
                    'report_slug': 'test-basic-report',
                    'report_page_id': 3,
                })
        )

        self.assertIn('Previous page', buttons)
        self.assertTrue(callable(buttons['Previous page']), msg="Previous page button content was not a function")
        self.assertEqual(
            buttons['Previous page'](view_obj),
            reverse(
                'setup:reports:pages:view_page',
                kwargs={
                    'report_slug': 'test-basic-report',
                    'report_page_id': 2,
                })
        )

    def test_init_view_params(self):
        # Create a basic class for which values need to be set
        class TestView:
            report_page = None
            page = None

        view_obj = TestView()
        report_site.init_view_params(view_obj, **{'report_page_id': 3})
        # report_page is set for continuity in this module
        self.assertEqual(view_obj.report_page, ReportPage.objects.get(id=3))
        # page needs to be set to work in the PageDisplay module
        self.assertEqual(view_obj.page, ReportPage.objects.get(id=3))

    def test_url_kwargs(self):
        class TestView:
            report_page = ReportPage.objects.get(id=2)

        view_obj = TestView()
        url_kwargs = report_site.get_url_kwargs(view_obj)
        self.assertEqual(url_kwargs['report_page_id'], 2)
        self.assertEqual(url_kwargs['report_slug'], 'test-basic-report')

    def test_delete_url(self):
        """ Test the url that is redirect to when this page has been deleted """
        page = ReportPage.objects.get(id=3)
        self.assertEqual(
            report_site.delete_success_url(page, **{'report_slug': 'test-basic-report'}),
            reverse('setup:reports:details', kwargs={'report_slug': 'test-basic-report'}),
            msg="Page deletion does not lead to neutral report page"
        )









