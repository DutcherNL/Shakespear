from django.test import TestCase

from . import override_media_folder
from reports.models import *
from reports.forms import *


class FormValidityMixin:
    form_class = None

    def get_form_kwargs(self, **kwargs):
        return kwargs

    def build_form(self, data, form_class=None, **kwargs):
        """ Builds the form, form_class can overwrite the default class attribute form_class """
        if form_class is None:
            form_class = self.form_class
        if form_class is None:
            raise KeyError("No form class is given, nor defined in the Testcase class")
        return form_class(data=data, **self.get_form_kwargs(**kwargs))

    def assertHasField(self, field_name):
        """
        Asserts that the form has a field with the given name
        :param field_name: name of the field
        :return: raises AssertionError if not asserted, otherwise returns empty
        """
        form = self.build_form({})
        self.assertIn(field_name, form.fields)

    def assertFormValid(self, data, form_class=None, **kwargs):
        """ Asserts that the form is valid otherwise raises AssertionError mentioning the form error
        :param data: The form data
        :param form_class: The form class, defaults to self.form_class
        :param kwargs: Any form init kwargs not defined in self.build_form()
        :return:
        """
        form = self.build_form(data, form_class=form_class, **kwargs)

        if not form.is_valid():
            fail_message = "The form was not valid. At least one error was encountered: "

            invalidation_errors = form.errors.as_data()
            error_key = list(invalidation_errors.keys())[0]
            invalidation_error = invalidation_errors[error_key][0]
            fail_message += f"'{invalidation_error.message}' in '{error_key}'"
            raise AssertionError(fail_message)
        return form

    def assertFormHasError(self, data, code, form_class=None, field=None, **kwargs):
        """ Asserts that a form with the given data invalidates on a certain error
        :param data: The form data
        :param code: the 'code' of the ValidationError
        :param form_class: The form class, defaults to self.form_class
        :param field: The field on which the validationerror needs to be, set to '__all__' if it's not form specefic
        leave empty if not relevant.
        :param kwargs: Any form init kwargs not defined in self.build_form()
        :return:
        """
        form = self.build_form(data, form_class=form_class, **kwargs)

        if form.is_valid():
            raise AssertionError("The form contained no errors")

        for key, value in form.errors.as_data().items():
            if field:
                if field != key:
                    continue
                for error in value:
                    if error.code == code:
                        return
                raise AssertionError(f"Form did not contain an error with code '{code}' in field '{field}'")
            else:
                for error in value:
                    if error.code == code:
                        return

        if field:
            raise AssertionError(f"Form did not encounter an error in '{field}'.'")

        error_message = f"Form did not contain an error with code '{code}'."
        if form.errors:
            invalidation_errors = form.errors.as_data()
            invalidation_error = invalidation_errors[list(invalidation_errors.keys())[0]][0]
            error_message += f" Though there was another error: '{invalidation_error}'"
        raise AssertionError(error_message)


class TestMovePageOrderForm(FormValidityMixin, TestCase):
    fixtures = ['test_report.json']
    form_class = MovePageForm

    def setUp(self):
        self.report = Report.objects.get(id=1)

    def get_form_kwargs(self, **kwargs):
        kwargs = super(TestMovePageOrderForm, self).get_form_kwargs(**kwargs)
        kwargs.update({
            'report': self.report,
        })
        return kwargs

    def test_fields(self):
        self.assertHasField('report_page')
        self.assertHasField('move_up')

    def test_report_validity(self):
        """ Tests that the page is part of the report when processing the form """
        # Page is part of this report
        self.assertFormValid({
            'report_page': 3,
            'move_up': False,
        })
        # Page is not part of this report
        self.assertFormHasError({
            'report_page': 6,
            'move_up': False,
        }, 'report_invalid')

    def test_move_up(self):
        form = self.assertFormValid({
            'report_page': 3,
            'move_up': True,
        })
        # Check the pages before the move (normal base state)
        pages = self.report.get_pages()
        self.assertEqual(pages[1].id, 4)
        self.assertEqual(pages[2].id, 3)
        # Switch the pages
        form.save()
        # Check pages after the move
        self.report.refresh_from_db()
        pages = self.report.get_pages()
        self.assertEqual(pages[1].id, 3)
        self.assertEqual(pages[2].id, 4)

    def test_move_up_as_first(self):
        self.assertFormHasError({
            'report_page': 2,
            'move_up': True,
        }, 'is_first_page')

    def test_move_down(self):
        form = self.assertFormValid({
            'report_page': 2,
            'move_up': False,
        })
        # Check the pages before the move (normal base state)
        pages = self.report.get_pages()
        self.assertEqual(pages[0].id, 2)
        self.assertEqual(pages[1].id, 4)
        # Switch the pages
        form.save()
        # Check pages after the move
        pages = self.report.get_pages()
        self.assertEqual(pages[0].id, 4)
        self.assertEqual(pages[1].id, 2)

    def test_move_down_as_last(self):
        self.assertFormHasError({
            'report_page': 5,
            'move_up': False,
        }, 'is_last_page')


@override_media_folder()
class TestAlterLayoutForm(FormValidityMixin, TestCase):
    fixtures = ['test_report.json']
    form_class = AlterLayoutForm
    # Note, this class tests with id=1 instance of PageLayout

    def get_form_kwargs(self, **kwargs):
        return super(TestAlterLayoutForm, self).get_form_kwargs(
            instance=PageLayout.objects.get(id=1),
            **kwargs
        )

    def test_initial_template_contents(self):
        self.assertHasField('contents')
        form = self.build_form(None)
        self.assertEqual(form.fields['contents'].initial, "<h1>New layout</h1>")

    def test_margins(self):
        self.assertHasField('margins')

    def test_template_content_saving(self):
        new_layout_content = '<p>This is a header</p>'
        form = self.assertFormValid({
            'margins': '20mm 40mm 40mm 20mm',
            'contents': new_layout_content,
        })
        form.save()
        self.assertEqual(PageLayout.objects.get(id=1).template_content, new_layout_content)
