from django.test import TestCase
from django.contrib import messages
from general.tests.mixins.test_view_mixins import *

from . import override_media_folder
from reports.setup.views import *


class ReportViewsMixin:
    """ Mixin that handles some data that is present in every test case """
    fixtures = ['test_report.json']
    url_namespace_prefix = "setup:reports:"


# #######################################################################
# ################       Basic Report Views       #######################
# #######################################################################

class TestReportMixin(ViewMixinTestMixin, TestCase):
    fixtures = ['test_report.json']
    view_mixin_class = ReportMixin

    def test_report(self):
        view = self.get_view_class(url_kwargs={'report_slug': 'test-basic-report'})
        # Test that a report is found
        self.assertEqual(view.report.id, 1)

        # Check context
        context = view.get_context_data()
        self.assertEqual(context['report'], view.report)


class TestReportOverView(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "reports_overview"

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/reports_overview.html")
        self.assertInContext(response, 'reports')

    def test_class(self):
        self.assertIsSubclass(ReportsOverview, AccessabilityMixin)
        self.assertIsSubclass(ReportsOverview, ListView)
        self.assertEqual(ReportsOverview.model, Report)
        self.assertEqual(ReportsOverview.context_object_name, 'reports')


class TestAddReportView(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "add_report"

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/report_form_add.html")

    def test_successful_post(self):
        response = self.build_post_response({
            'report_name': 'test-post-report',
            'description': 'some description',
            'file_name': 'some-file-name'
        }, follow=True)

        self.assertRedirects(response, reverse('setup:reports:details', kwargs={'report_slug': 'test-post-report'}))

        try:
            ReportDisplayOptions.objects.get(report__report_name='test-post-report')
        except ReportDisplayOptions.DoesNotExist:
            raise AssertionError('ReportDisplayOptions is not created upon report creation')

    def test_class(self):
        self.assertIsSubclass(AddReportView, AccessabilityMixin)
        self.assertIsSubclass(AddReportView, CreateView)
        self.assertEqual(AddReportView.model, Report)


class TestReportInfoView(ViewTestMixin, TestCase):
    fixtures = ['test_report.json']
    url_namespace_prefix = "setup:reports:"
    default_url_name = "details"
    default_url_kwargs = {'report_slug': "test-basic-report"}

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/report_detail.html")

    def test_class(self):
        self.assertIsSubclass(ReportInfoView, ReportMixin)
        self.assertIsSubclass(ReportInfoView, AccessabilityMixin)


class TestEditReportView(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "edit_report"
    default_url_kwargs = {'report_slug': "test-basic-report"}

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/report_form.html")

        # Report form uses this open attribute in the breadcrumbs for versatility of the form
        self.assertInContext(response, 'crumb_name', instance='Edit general settings')

    def test_successful_post(self):
        response = self.build_post_response({
            'report_name': 'new-report-name',
            'description': 'some description',
            'file_name': 'some-file-name',
            'display_order': 1,
        }, follow=True)

        print(response)

        try:
            Report.objects.get(report_name='new-report-name')
        except Report.DoesNotExist:
            raise AssertionError("Report name was not adjusted")

        self.assertRedirects(response, reverse('setup:reports:details', kwargs={'report_slug': 'new-report-name'}))

    def test_class(self):
        self.assertIsSubclass(ReportUpdateView, AccessabilityMixin)
        self.assertIsSubclass(ReportUpdateView, UpdateView)
        self.assertEqual(ReportUpdateView.model, Report)
        self.assertIn('report_name', ReportUpdateView.fields)
        self.assertIn('description', ReportUpdateView.fields)
        self.assertIn('promotion_text', ReportUpdateView.fields)
        self.assertIn('file_name', ReportUpdateView.fields)
        self.assertIn('is_live', ReportUpdateView.fields)


class TestEditReportDisplayOptionsView(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "edit_display"
    default_url_kwargs = {'report_slug': "test-basic-report"}

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/report_form.html")

        # Report form uses this open attribute in the breadcrumbs for versatility of the form
        self.assertInContext(response, 'crumb_name', instance='Edit display options')

    def test_successful_post(self):
        response = self.build_post_response({
            'size': 'A4',
            'orientation': 'True',
            'margins': '20mm 20mm 20mm 20mm',
            'header': 'new-header text',
            'footer': 'new-footer text',
        }, follow=True)

        try:
            ReportDisplayOptions.objects.get(header='new-header text', report_id=1)
        except ReportDisplayOptions.DoesNotExist:
            raise AssertionError("Report name was not adjusted")

        self.assertRedirects(response, reverse('setup:reports:details', kwargs={'report_slug': 'test-basic-report'}))

    def test_class(self):
        self.assertIsSubclass(ReportDisplayOptionsUpdateView, AccessabilityMixin)
        self.assertIsSubclass(ReportDisplayOptionsUpdateView, UpdateView)
        self.assertEqual(ReportDisplayOptionsUpdateView.model, ReportDisplayOptions)
        self.assertEqual(ReportDisplayOptionsUpdateView.fields, '__all__')


# #######################################################################
# ################       Basic Layout Views       #######################
# #######################################################################


@override_media_folder()
class TestLayoutListView(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "layout_overview"
    default_url_kwargs = {'report_slug': "test-basic-report"}

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/layouts/layout_overview.html")
        self.assertInContext(response, 'preview_width', instance=10)
        self.assertInContext(response, 'preview_height', instance=10 * 297.2 / 210)
        self.assertInContext(response, 'preview_scale', instance=0.4)

    def test_get_queryset(self):
        # Set up basic view instance proporties to make it work
        view = ReportLayoutListView()
        view.report = Report.objects.get(slug='test-basic-report')

        queryset = view.get_queryset()
        self.assertEqual(len(queryset), 1)
        self.assertIsInstance(queryset.first(), PageLayout)
        self.assertEqual(queryset.first().id, 1)

    def test_class(self):
        self.assertIsSubclass(ReportLayoutListView, AccessabilityMixin)
        self.assertIsSubclass(ReportLayoutListView, ListView)


@override_media_folder()
class TestAddLayoutView(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "add_layout"
    default_url_kwargs = {'report_slug': "test-basic-report"}

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/layouts/create_layout.html")

    def test_successful_post(self):
        response = self.build_post_response({
            'name': 'new-layout',
            'description': 'some description',
            'margins': '20mm 20mm 20mm 20mm'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        try:
            layout = PageLayout.objects.get(name='new-layout')
        except PageLayout.DoesNotExist:
            raise AssertionError("Post did not create a new page layout")

        # Report is set through code instead of POST data, so check if that works
        self.assertEqual(layout.report_id, 1)

        self.assertRedirects(response,
                             reverse('setup:reports:edit_layout',
                                     kwargs={'report_slug': 'test-basic-report', 'layout': layout}
                                     ))

    def test_class(self):
        self.assertIsSubclass(ReportAddLayoutView, AccessabilityMixin)
        self.assertIsSubclass(ReportAddLayoutView, ReportMixin)
        self.assertIsSubclass(ReportAddLayoutView, CreateView)
        self.assertEqual(ReportAddLayoutView.model, PageLayout)


@override_media_folder()
class TestLayoutMixin(ViewMixinTestMixin, TestCase):
    fixtures = ['test_report.json']
    view_mixin_class = [ReportMixin, LayoutMixin]

    def test_valid_layout(self):
        layout = PageLayout.objects.get(id=1)
        view = self.get_view_class(url_kwargs={'report_slug': 'test-basic-report', 'layout': layout})

        # Check context
        context = view.get_context_data()
        self.assertEqual(context['layout'], layout)

    def test_invalid_layout(self):
        # Tests that it raises a 404 when the layout is not part of the report
        layout = PageLayout.objects.get(id=1)
        try:
            view = self.get_view_class(url_kwargs={'report_slug': 'another-report', 'layout': layout})
        except Http404:
            pass
        else:
            raise AssertionError("LayoutMixin did not fail when layout ")


@override_media_folder()
class TestPreviewLayoutMixin(ViewMixinTestMixin, TestCase):
    fixtures = ['test_report.json']
    view_mixin_class = [ReportMixin, LayoutMixin, PreviewLayoutMixin]

    def test_context_data(self):
        layout = PageLayout.objects.get(id=1)
        view = self.get_view_class(url_kwargs={'report_slug': 'test-basic-report', 'layout': layout})
        context_data = view.get_context_data()
        report_display_options = layout.report.display_options

        self.assertIn('layout_context', context_data)
        self.assertIn('header', context_data['layout_context'])
        self.assertIn('footer', context_data['layout_context'])
        self.assertIn('measurements', context_data)
        self.assertIn('margins', context_data['measurements'])
        self.assertIn('size', context_data['measurements'])

        self.assertEqual(context_data['layout_context']['header'], report_display_options.header)
        self.assertEqual(context_data['layout_context']['footer'], report_display_options.footer)
        self.assertEqual(context_data['measurements']['margins'], layout.margins)
        self.assertEqual(context_data['measurements']['size'], report_display_options.paper_proportions)


@override_media_folder()
class TestEditLayoutView(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "edit_layout"
    default_url_kwargs = {'report_slug': "test-basic-report", 'layout': 1}

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/layouts/edit_layout.html")

    def test_successful_post(self):
        response = self.build_post_response({
            'contents': '<h1>New layout</h1>',
            'margins': '20mm 20mm 20mm 20mm'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.build_url())

        layout = PageLayout.objects.get(id=1)
        self.assertEqual(layout.template_content, '<h1>New layout</h1>')

    def test_class(self):
        self.assertIsSubclass(ReportChangeLayoutView, AccessabilityMixin)
        self.assertIsSubclass(ReportChangeLayoutView, ReportMixin)
        self.assertIsSubclass(ReportChangeLayoutView, LayoutMixin)
        self.assertIsSubclass(ReportChangeLayoutView, PreviewLayoutMixin)
        self.assertIsSubclass(ReportChangeLayoutView, FormView)
        self.assertEqual(ReportChangeLayoutView.form_class, AlterLayoutForm)


@override_media_folder()
class TestEditLayoutSettingsView(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "edit_layout_settings"
    default_url_kwargs = {'report_slug': "test-basic-report", 'layout': 1}

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/layouts/edit_layout_settings.html")

    def test_successful_post(self):
        response = self.build_post_response({
            'name': 'A new name',
            'description': 'some description'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.build_url(url_name='edit_layout'))

        layout = PageLayout.objects.get(id=1)
        self.assertEqual(layout.name, 'A new name')

    def test_class(self):
        self.assertIsSubclass(ReportChangeLayoutSettingsView, AccessabilityMixin)
        self.assertIsSubclass(ReportChangeLayoutSettingsView, ReportMixin)
        self.assertIsSubclass(ReportChangeLayoutSettingsView, LayoutMixin)
        self.assertIsSubclass(ReportChangeLayoutSettingsView, PreviewLayoutMixin)
        self.assertIsSubclass(ReportChangeLayoutSettingsView, UpdateView)
        self.assertIn('name', ReportChangeLayoutSettingsView.fields)
        self.assertIn('description', ReportChangeLayoutSettingsView.fields)


# #######################################################################
# ################        Page Setup Views        #######################
# #######################################################################


class TestAddSinglePageView(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "add_page"
    default_url_kwargs = {'report_slug': "test-basic-report"}

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/reportpage_form_add.html")

    def test_successful_post(self):
        response = self.build_post_response({
            'name': 'a whole new page',
            'description': 'new page description',
            'layout': 1,
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        try:
            page = ReportPageSingle.objects.get(name='a whole new page')
        except PageLayout.DoesNotExist:
            raise AssertionError("Post did not create a new page")

        page_detail_url = reverse(
            'setup:reports:details',
            kwargs={'report_slug': 'test-basic-report', 'report_page_id': page.id}
        )
        self.assertRedirects(response,page_detail_url)

    def test_link_creation(self):
        self.build_post_response({
            'name': 'a whole new page',
            'description': 'new page description',
            'layout': 1,
        }, follow=True)
        link = ReportPageLink.objects.get(page__name="a whole new page")
        self.assertIsNotNone(link, msg="Reportpagelink was not initialised to the new page")
        self.assertEqual(link.report.id, 1, msg="Reportpage id was not set correctly")
        self.assertEqual(link.page_number, 8,
                         msg=f'Pagenumber of new page was set to {link.page_number} instead of 8 (last page + 1)')

    def test_link_creation_first_page(self):
        # Ensure there are no pages in the report
        ReportPageLink.objects.filter(report__slug="test-basic-report").delete()
        self.build_post_response({
            'name': 'a whole new page',
            'description': 'new page description',
            'layout': 1,
        }, follow=True)
        link = ReportPageLink.objects.get(page__name="a whole new page")
        self.assertIsNotNone(link, msg="Reportpagelink was not initialised to the new page")
        self.assertEqual(link.report.id, 1, msg="Reportpage id was not set correctly")
        self.assertEqual(link.page_number, 1,
                         msg=f'When no page is present, new page_number should be 1, but it was {link.page_number}')

    def test_class(self):
        self.assertIsSubclass(CreateReportPageView, AccessabilityMixin)
        self.assertIsSubclass(CreateReportPageView, ReportMixin)
        self.assertIsSubclass(CreateReportPageView, CreateView)
        self.assertEqual(CreateReportPageView.model, ReportPage)
        self.assertIn('name', CreateReportPageView.fields)
        self.assertIn('description', CreateReportPageView.fields)
        self.assertIn('layout', CreateReportPageView.fields)


class TestMovePageView(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "move_page"
    default_url_kwargs = {'report_slug': "test-basic-report"}

    def test_get_method(self):
        # There is no GET method for this page, only POST
        response = self.build_get_response()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.build_url(url_name='details'))

    def test_successful_post(self):
        response = self.build_post_response({
            'report_page': 3,
            'move_up': True,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.build_url(url_name='details'))
        self.assertHasMessage(response, messages.SUCCESS, text="Succesfully moved 3rd page upward")

        self.assertEqual(ReportPageLink.objects.get(page_id=3).page_number, 3)

    def test_unsuccessful_post(self):
        # This page is the first page and can't be moved up
        response = self.build_post_response({
            'report_page': 2,
            'move_up': True,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, self.build_url(url_name='details'))
        self.assertHasMessage(response, messages.ERROR)
        self.assertEqual(ReportPageLink.objects.get(page_id=2).page_number, 1)

    def test_class(self):
        self.assertIsSubclass(ReportMovePageView, AccessabilityMixin)
        self.assertIsSubclass(ReportMovePageView, ReportMixin)
        self.assertIsSubclass(ReportMovePageView, FormView)
        self.assertEqual(ReportMovePageView.form_class, MovePageForm)


class TestAddMultiPageView(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "add_multi_page"
    default_url_kwargs = {'report_slug': "test-basic-report"}

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/reportpage_form_add.html")

    def test_successful_post(self):
        response = self.build_post_response({
            'name': 'a whole new multi-page',
            'description': 'new multi-page description',
            'multi_type': ReportPageMultiGenerated.TECHS_ADVISED,
            'layout': 1,
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        try:
            page = ReportPageMultiGenerated.objects.get(name='a whole new multi-page')
        except PageLayout.DoesNotExist:
            raise AssertionError("Post did not create a new page")

        page_detail_url = reverse(
            'setup:reports:details',
            kwargs={'report_slug': 'test-basic-report', 'report_page_id': page.id}
        )
        self.assertRedirects(response, page_detail_url)

    def test_link_creation(self):
        self.build_post_response({
            'name': 'a whole new multi-page',
            'description': 'new multi-page description',
            'multi_type': ReportPageMultiGenerated.TECHS_ADVISED,
            'layout': 1,
        }, follow=True)
        link = ReportPageLink.objects.get(page__name="a whole new multi-page")
        self.assertIsNotNone(link, msg="Reportpagelink was not initialised to the new page")
        self.assertEqual(link.report.id, 1, msg="Reportpage id was not set correctly")
        self.assertEqual(link.page_number, 8,
                         msg=f'Pagenumber of new page was set to {link.page_number} instead of 8 (last page + 1)')

    def test_link_creation_first_page(self):
        # Ensure there are no pages in the report
        ReportPageLink.objects.filter(report__slug="test-basic-report").delete()
        self.build_post_response({
            'name': 'a whole new multi-page',
            'description': 'new page description',
            'multi_type': ReportPageMultiGenerated.TECHS_ADVISED,
            'layout': 1,
        }, follow=True)
        link = ReportPageLink.objects.get(page__name="a whole new multi-page")
        self.assertIsNotNone(link, msg="Reportpagelink was not initialised to the new page")
        self.assertEqual(link.report.id, 1, msg="Reportpage id was not set correctly")
        self.assertEqual(link.page_number, 1,
                         msg=f'When no page is present, new page_number should be 1, but it was {link.page_number}')

    def test_class(self):
        self.assertIsSubclass(CreateReportMultiPageView, AccessabilityMixin)
        self.assertIsSubclass(CreateReportMultiPageView, ReportMixin)
        self.assertIsSubclass(CreateReportMultiPageView, CreateView)
        self.assertEqual(CreateReportMultiPageView.model, ReportPage)
        self.assertIn('name', CreateReportMultiPageView.fields)
        self.assertIn('description', CreateReportMultiPageView.fields)
        self.assertIn('layout', CreateReportMultiPageView.fields)
        self.assertIn('multi_type', CreateReportMultiPageView.fields)


class TestReportPageMixin(ViewMixinTestMixin, TestCase):
    fixtures = ['test_report.json']
    view_mixin_class = ReportPageMixin

    def test_report(self):
        view = self.get_view_class(url_kwargs={
            'report_slug': 'test-basic-report',
            'report_page_id': 2,
        })
        # Test that a report is found
        self.assertEqual(view.report_page.id, 2)

        # Check context
        context = view.get_context_data()
        self.assertEqual(context['report_page'], view.report_page)

    def test_class(self):
        self.assertTrue(issubclass(self.view_mixin_class, AccessabilityMixin),
                        msg=f"{self.view_mixin_class} does not inherit from AccessibilityMixin class")
        self.assertTrue(issubclass(self.view_mixin_class, ReportMixin),
                        msg=f"{self.view_mixin_class} does not inherit from ReportMixin class")

# All other relevant views are part of the PageDisplay site object and thus not tested there

# #######################################################################
# ################      Page Criteria Views       #######################
# #######################################################################


class TestCriteriaOverview(ReportViewsMixin, ViewTestMixin, TestCase):
    default_url_name = "page_criterias"
    default_url_kwargs = {'report_slug': "test-basic-report", 'report_page_id': 3}

    def test_get_method(self):
        response = self.build_get_response()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/setup/page_conditions/reportpage_criteria_list.html")

    def test_get_queryset(self):
        # Todo: Add criteria data to dataset
        # Set up basic view instance proporties to make it work
        view = ReportLayoutListView()
        view.report_page = ReportPage.objects.get(id=3)

        queryset = view.get_queryset()
        self.assertEqual(len(queryset), 0)

    def test_class(self):
        self.assertIsSubclass(ReportPageCriteriaOverview, ReportPageMixin)
        self.assertIsSubclass(ReportPageCriteriaOverview, ListView)

# Todo other criteria test classes
