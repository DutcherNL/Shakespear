import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.conf import settings

from DataStorage.models import *
from DataStorage.forms import DataUploadForm
from . import DataTestingMixin


# Create your tests here.


class CSVFormTestCase(DataTestingMixin, TestCase):
    """ Tests the workings of the CSVFormTestCase """

    @staticmethod
    def build_file_dict(file_name):
        file_path = os.path.join(settings.BASE_DIR, f'DataStorage\\tests\\csv_test_files\\{file_name}')
        upload_file = open(file_path, 'rb')
        return {'csv_file': SimpleUploadedFile(upload_file.name, upload_file.read())}

    def test_form_deliminator_validity(self):
        # Test the base case
        post_dict = {'deliminator': ',', 'name': 'test_batch'}
        file_dict = self.build_file_dict('valid_base_test.csv')
        self.assertTrue(DataUploadForm(post_dict, file_dict).is_valid())

        # Test a different deliminator
        post_dict = {'deliminator': ';', 'name': 'test_batch'}
        self.assertFalse(DataUploadForm(post_dict, file_dict).is_valid())

        # Test a different file with the different deliminator
        file_dict = self.build_file_dict('valid_delim_test.csv')
        form = DataUploadForm(post_dict, file_dict)
        self.assertTrue(form.is_valid())

    def test_extention_validity(self):
        """ Tests whether a check is done on uploaded file extentions """
        post_dict = {'deliminator': ',', 'name': 'test_batch'}
        file_dict = self.build_file_dict('valid_but_wrong_extension_test.txt')
        # File ends with .txt instead of csv so it should bounce
        self.assertFalse(DataUploadForm(post_dict, file_dict).is_valid())

    def test_form_code_validity(self):
        """ Tests whether a file with an invalid code_name will bounce """
        post_dict = {'deliminator': ',', 'name': 'test_batch'}
        file_dict = self.build_file_dict('invalid_code_declaration.csv')
        # File contains postal_code instead of postcode and should therefore not be deemed valid
        self.assertFalse(DataUploadForm(post_dict, file_dict).is_valid())

        file_dict = self.build_file_dict('invalid_data_declaration.csv')
        # File contains property_1 instead of eigenschap_1 and should therefore not be deemed valid
        self.assertFalse(DataUploadForm(post_dict, file_dict).is_valid())

        # Note:
        # Too ease load on cleaning, each entry is NOT cleaned. Instead it will throw key errors when errors occur

    def test_csv_form_saving(self):
        # Test the base case
        batch_name = 'test_batch_1'
        post_dict = {'deliminator': ',', 'name': batch_name}
        file_dict = self.build_file_dict('valid_base_test.csv')
        save_result = DataUploadForm(post_dict, file_dict).save()

        # Test the returned results. It should be the Batch object followed by a list of all incorrect entries
        # In this example, there are no incorrect entries
        self.assertEqual(save_result[1]['codes'], [])
        self.assertEqual(save_result[1]['empty'], [])
        self.assertEqual(save_result[1]['incomplete'], [])

        self.assertExists(StoredDataCode, code_type=self.sdcd_1, identification_code="1234AB")
        self.assertExists(StoredDataContent,
                          code__identification_code="1234AB",
                          batch__name=batch_name,
                          data_declaration__name="eigenschap_1",
                          content=10)
        self.assertExists(StoredDataContent,
                          code__identification_code="1234AC",
                          batch__name=batch_name,
                          data_declaration__name="eigenschap_2",
                          content="Some string")

        """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""
        """         TEST 2, TEST DATA CHANGES                    """
        """         Test changing of earlier processed data      """
        """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""

        batch_name = 'test_batch_2'
        post_dict = {'deliminator': ',', 'name': batch_name}
        file_dict = self.build_file_dict('valid_base_test 2.csv')
        save_result = DataUploadForm(post_dict, file_dict).save()

        # This content should have been changed and overwritten
        self.assertNotExists(StoredDataContent,
                             code__identification_code="1234AC",
                             data_declaration__name="eigenschap_2",
                             content="Some string")
        # Assert that the correct object still exists
        self.assertExists(StoredDataContent,
                          code__identification_code="1234AC",
                          batch__name=batch_name,
                          data_declaration__name="eigenschap_2",
                          content="Changed")

        # Test the returned results. This test should contain 1 wrong answer ('wrong')
        self.assertEqual(len(save_result[1]['codes']), 1)
        self.assertEqual(save_result[1]['codes'][0], "wrong")
        self.assertNotExists(StoredDataContent,
                             code__identification_code="wrong",
                             data_declaration__name="eigenschap_1")

        """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
        """         TEST 3, TEST (PARTIALLY) INCORRECT ENTRIES     """
        """         This part checks if incomplete entries are     """
        """         processed correctly                            """
        """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

        batch_name = 'test_batch_3'
        post_dict = {'deliminator': ',', 'name': batch_name}
        file_dict = self.build_file_dict('valid_base_test 3.csv')
        save_result = DataUploadForm(post_dict, file_dict).save()

        # This one should not have changed (entry did not exist)
        self.assertExists(StoredDataContent,
                          code__identification_code="1234AC",
                          data_declaration__name="eigenschap_2",
                          content="Changed")
        self.assertEqual(len(save_result[1]['incomplete']), 2)
        self.assertEqual(save_result[1]['incomplete'][0], "1234AC")

        # The contents delivered are empty, so don't overwrite it
        # exact value has been checked with earlier tests, it is assumed that the following check suffices.
        self.assertNotExists(StoredDataContent,
                             code__identification_code="1234AB",
                             data_declaration__name="eigenschap_1",
                             batch__name=batch_name)
        self.assertExists(StoredDataContent,
                             code__identification_code="1234AB",
                             data_declaration__name="eigenschap_1")
        # Ensure that the second entry was processed
        self.assertExists(StoredDataContent,
                          code__identification_code="1234AB",
                          data_declaration__name="eigenschap_2",
                          content="20")
        self.assertEqual(len(save_result[1]['empty']), 1)
        self.assertEqual(save_result[1]['empty'][0], "1234AB")

        # Ensure last line processing (an encountered error should not stop the remainder entries from processing
        # Assert that it did process all entries by checking the existance of the last entry
        self.assertExists(StoredDataContent,
                          code__identification_code="1234AD",
                          batch__name=batch_name,
                          data_declaration__name="eigenschap_1")

    @staticmethod
    def assertExists(model, **kwargs):
        if not model.objects.filter(**kwargs).exists():
            raise AssertionError(f'There is no object of \"{model.__name__}\" that adheres the following properties:'
                                 f'{kwargs}')

    @staticmethod
    def assertNotExists(model, **kwargs):
        if model.objects.filter(**kwargs).exists():
            raise AssertionError(f'There is an object of \"{model.__name__}\" that adheres the following properties:'
                                 f'{kwargs}')
