from django.test import TestCase

from PageDisplay.models import Page
from PageDisplay.module_registry import registry
from PageDisplay.renderers import BasePageRenderer

from reports import renderers
from reports.models import *
from reports.sites import report_site
from reports.forms import SelectPageLayoutForm


class TestPageRendererMixin:
    renderer_class = None
    report_page_id = None

    def setUp(self):
        if self.report_page_id:
            self.renderer = self.renderer_class(page=Page.objects.get(id=3))
        else:
            self.renderer = self.renderer_class()
        super(TestPageRendererMixin, self).setUp()

    def assertUsesWidget(self, module, widget, renderer=None):
        if isinstance(module, type):
            module_name = str(module.__class__)
        else:
            module_name = str(module)

        if renderer is None:
            renderer = self.renderer

        widget_dict = renderer.replaced_widgets_dict

        overwrite_widget = widget_dict.get(module, None)
        if overwrite_widget is None:
            module = registry.get_module_from_name(module_name)
            if isinstance(widget, str):
                widget_correct = module.widget.__name__ == widget
            else:
                widget_correct = module.widget == widget

            if not widget_correct:
                raise AssertionError(f"Module '{module_name}' has no widget set and the default widget is not the desired"
                                     f" widget, but uses '{module.widget}' instead")
        else:
            if isinstance(widget, str):
                widget_correct = overwrite_widget.__name__ == widget
            else:
                widget_correct = overwrite_widget == widget
            if not widget_correct:
                raise AssertionError(f"Module '{module_name}' is overwritten with {overwrite_widget} instead of {widget}")


class TestReportRenderingMixin(TestCase):
    fixtures = ['test_report.json']

    def setUp(self):
        class TestRenderer(renderers.ReportRenderingMixin, BasePageRenderer):
            pass
        self.report_page = ReportPage.objects.get(id=3)
        self.renderer = TestRenderer(page=self.report_page)

    def test_context_data(self):
        context_data = self.renderer.get_context_data()
        report_display_options = ReportDisplayOptions.objects.get(report_id=1)
        self.assertIn('measurements', context_data)
        self.assertIn('margins', context_data['measurements'])
        self.assertIn('size', context_data['measurements'])
        self.assertEqual(context_data['measurements']['margins'], '20mm 20mm 20mm 20mm')
        self.assertEqual(context_data['measurements']['size'], report_display_options.paper_proportions)

        self.assertIn('layout_context', context_data)
        self.assertIn('header', context_data['layout_context'])
        self.assertIn('footer', context_data['layout_context'])
        self.assertIn('p_num', context_data['layout_context'])
        self.assertEqual(context_data['layout_context']['header'], report_display_options.header)
        self.assertEqual(context_data['layout_context']['footer'], report_display_options.footer)
        self.assertEqual(context_data['layout_context']['p_num'], 1)


class TestSinglePageRenderer(TestPageRendererMixin, TestCase):
    fixtures = ['test_report.json']
    renderer_class = renderers.ReportSinglePageRenderer
    report_page_id = 3

    def test_class(self):
        self.assertUsesWidget('TechScoreModule', 'TechScorePreviewPDFWidget')
        self.assertEqual(self.renderer_class.template_name, "reports/page_display/papersize_container.html")
        self.assertIsInstance(self.renderer, renderers.ReportRenderingMixin)


class TestSinglePagePDFRenderer(TestPageRendererMixin, TestCase):
    fixtures = ['test_report.json']
    renderer_class = renderers.ReportSinglePagePDFRenderer
    report_page_id = 3

    def test_class(self):
        self.assertUsesWidget('ImageModule', 'ImagePDFWidget')
        self.assertUsesWidget('TechScoreModule', 'TechScorePDFWidget')
        self.assertEqual(self.renderer_class.template_name, "reports/page_display/papersize_container.html")
        self.assertIsInstance(self.renderer, renderers.ReportRenderingMixin)


class TestMultiPageRenderer(TestPageRendererMixin, TestCase):
    fixtures = ['test_report.json']
    renderer_class = renderers.ReportMultiPageRenderer
    report_page_id = 3

    def test_class(self):
        self.assertUsesWidget('TechScoreModule', 'TechScoreFromIterableWidget')
        self.assertEqual(self.renderer_class.template_name,
                         "reports/page_display/papersize_container_multigenerated.html")
        self.assertIsInstance(self.renderer, renderers.ReportRenderingMixin)

    def test_elements(self):
        # Todo
        # Also include check for context data
        pass


class TestMultiPagePDFRenderer(TestPageRendererMixin, TestCase):
    fixtures = ['test_report.json']
    renderer_class = renderers.ReportMultiPagePDFRenderer
    report_page_id = 3

    def test_class(self):
        self.assertUsesWidget('ImageModule', 'ImagePDFWidget')
        self.assertUsesWidget('TechScoreModule', 'TechScoreFromIterablePDFWidget')
        self.assertEqual(self.renderer_class.template_name,
                         "reports/page_display/papersize_container_multigenerated.html")
        self.assertIsInstance(self.renderer, renderers.ReportRenderingMixin)

