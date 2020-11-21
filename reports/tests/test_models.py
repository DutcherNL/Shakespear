from copy import copy

from django.test import TestCase
from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from . import create_overwrite_media_folder_decorator
from reports.models import *


override_media_folder = create_overwrite_media_folder_decorator('reports')


class ModelTestCaseMixin:
    test_class = None
    required_fields = {}

    def test_has_fields(self):
        # If no required fields are set, return it. No need to
        if not self.required_fields:
            return

        fields = copy(self.required_fields)

        for model_field in self.test_class._meta.fields:
            if model_field.name in fields.keys():
                if model_field.__class__ == fields[model_field.name]:
                    del fields[model_field.name]

        if fields:
            raise AssertionError(
                f"There are still one or more required fields not set-up correctly on class {self.test_class}:{fields}")

    def assertIsClean(self, model):
        try:
            model.clean()
        except ValidationError as e:
            raise AssertionError(f"Model was not clean: {e}")

    def assertIsNotClean(self, model, expected_error_code):
        try:
            model.clean()
        except ValidationError as e:
            if e.code == expected_error_code:
                return
            else:
                raise AssertionError(f"Model did not raise error with code {expected_error_code}, but {e.code} instead")
        raise AssertionError("Model was clean where it was not expected to be")


@override_media_folder()
class TestReportModel(ModelTestCaseMixin, TestCase):
    """ Tests the report model """
    fixtures = ['test_report.json']
    test_class = Report
    required_fields = {
        'report_name': models.CharField,
        'file_name': models.CharField,
        'promotion_text': models.TextField,
        'is_live': models.BooleanField,
    }

    def test_slug_saving(self):
        """ Asserts that the slug is made automatically from the name """
        report = Report(report_name="Test report slug")
        report.save()
        self.assertEqual(report.slug, "test-report-slug")

    def test_get_pages(self):
        """ Method should return all pages in the correct order """
        pages = Report.objects.get(id=1).get_pages()

        # correct number of pages
        self.assertEqual(len(pages), 4)
        # Test that the order is correct
        self.assertEqual(pages[0].name, "First page")
        self.assertEqual(pages[1].name, "2nd page")
        self.assertEqual(pages[2].name, "3rd page")


@override_media_folder()
class TestPageLayoutModel(ModelTestCaseMixin, TestCase):
    fixtures = ['test_report.json']

    test_class = PageLayout
    required_fields = {
        'report': models.ForeignKey,
        'name': models.CharField,
        'template': models.FileField,
        'margins': models.CharField,
    }

    def setUp(self):
        self.report = Report.objects.get(id=1)

    def test_slug_saving(self):
        """ Asserts that the slug is made automatically from the name """
        layout = PageLayout(
            name="Test slug layout",
            report=self.report,
        )
        layout.save()
        self.assertEqual(layout.slug, "test-slug-layout")

    def test_template_content(self):
        layout = PageLayout.objects.get(id=1)
        self.assertEqual(layout.template_content, "<div>Plain header</div>")

    def test_file_extension(self):
        """ Tests allowed file extensions """
        # These extensions are not allowed
        for ext in ['doc', 'oml']:
            template_file = SimpleUploadedFile(f'non-valid-file.{ext}', b'This is not valid')
            layout = PageLayout(
                name="non-valid-layout",
                template=template_file,
            )
            self.assertIsNotClean(layout, "Invalid extension")

        # These extensions are allowed
        for ext in ['html', 'txt']:
            template_file = SimpleUploadedFile(f'non-valid-file.{ext}', b'This is not valid')
            layout = PageLayout(
                name="non-valid-layout",
                template=template_file,
            )
            self.assertIsClean(layout)


@override_media_folder()
class TestDisplayOptionsModel(ModelTestCaseMixin, TestCase):
    test_class = ReportDisplayOptions
    required_fields = {
        'report': models.OneToOneField,
        'size': models.CharField,
        'orientation': models.BooleanField,
        'header': models.CharField,
        'footer': models.CharField,
    }

    def test_paper_sizes(self):
        results = {
            'A3': {'width': 297, 'height': 420},
            'A4': {'width': 210, 'height': 297.2},  # Aligned with render engine, small offset escalates over many pages
            'A5': {'width': 148, 'height': 210},
        }
        for key, value in results.items():
            display = ReportDisplayOptions(
                report_id=1,
                orientation=True,
                size=key
            )
            compute = display.get_paper_sizes_mm()
            self.assertEqual(value['width'], compute['width'])
            self.assertEqual(value['height'], compute['height'])

    def test_paper_proportions(self):
        proportions = ReportDisplayOptions(
            report_id=1,
            orientation=False,
            size='A4'
        ).paper_proportions

        self.assertEqual(proportions['width'], '297.2mm')
        self.assertEqual(proportions['height'], '210mm')


@override_media_folder()
class TestReportPageModel(ModelTestCaseMixin, TestCase):
    fixtures = ['test_report.json']
    test_class = ReportPage
    required_fields = {
        'layout': models.ForeignKey,
    }

    def test_get_as_child(self):
        """ Tests the get_as_child method """
        page = ReportPage.objects.get(id=3).get_as_child()
        self.assertEqual(page.__class__, ReportPageSingle)
        # Todo: add multi report page


@override_media_folder()
class TestReportPageSingleModel(ModelTestCaseMixin, TestCase):
    fixtures = ['test_report.json']

    def test_queryset_manager(self):
        """ Test that only single-pages are returned """
        self.assertEqual(ReportPageSingle.objects.count(), 4)

    def test_get_num_plotted_pages(self):
        self.assertEqual(ReportPageSingle.objects.first().get_num_plotted_pages(None), 1)


@override_media_folder()
class TestReportPageMutliModel(ModelTestCaseMixin, TestCase):
    fixtures = ['test_report.json']
    test_class = ReportPageMultiGenerated
    required_fields = {
        'multi_type': models.IntegerField,
    }

    def test_queryset_manager(self):
        """ Test that only multi-pages are returned """
        self.assertEqual(ReportPageMultiGenerated.objects.count(), 0)

    def test_get_num_plotted_pages(self):
        # Todo
        pass


@override_media_folder()
class TestPageLinkModel(ModelTestCaseMixin, TestCase):
    fixtures = ['test_report.json']
    test_class = ReportPageLink
    required_fields = {
        'report': models.ForeignKey,
        'page': models.OneToOneField,
        'page_number': models.PositiveIntegerField,
    }




