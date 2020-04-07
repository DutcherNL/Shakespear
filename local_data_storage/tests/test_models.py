from django.test import TestCase
from django.forms import ValidationError

from local_data_storage.models import DataTable, DataColumn, DataContent
from . import DataTestingMixin

# Create your tests here.


class DataModelTestCase(DataTestingMixin, TestCase):
    @staticmethod
    def assertNotClean(model, *args, **kwargs):
        """
        Executes a bit of code with the given arguments and asserts a validationerror occurs
        :param code: A method
        :param args: The arguments of that method
        :param kwargs: The keyword arguments of that method
        :return:
        """
        try:
            model.full_clean(*args, **kwargs)
        except ValidationError as v:
            # A validation error was intercepted, so this goes well
            return
        else:
            raise AssertionError('No ValidationError occured')

    @staticmethod
    def assertClean(model, *args, **kwargs):
        try:
            model.full_clean(*args, **kwargs)
        except ValidationError as error:
            raise AssertionError(f'Unexpected ValidationError occured: {error.messages}')

    def test_regex_validitiy(self):
        # Test that regex validity is uphold
        # self.assertClean(StoredDataCode(code_type=self.sdcd_1, identification_code='1234AB'))
        # self.assertClean(StoredDataCode(code_type=self.sdcd_1, identification_code='9999ZZ'))
        #
        # # These all should throw validation errors for non-matching regex patterns
        # self.assertNotClean(  # Test incomplete validity
        #     StoredDataCode(code_type=self.sdcd_1, identification_code='1234'))
        # self.assertNotClean(  # Test incorrect number of elements
        #     StoredDataCode(code_type=self.sdcd_1, identification_code='567AI'))
        # self.assertNotClean(  # Test incorrect imput elements
        #     StoredDataCode(code_type=self.sdcd_1, identification_code='2589nm'))
        # self.assertNotClean(  # Test start marker workings
        #     StoredDataCode(code_type=self.sdcd_1, identification_code='not 8765AB'))
        # self.assertNotClean(  # Test end marker workings
        #     StoredDataCode(code_type=self.sdcd_1, identification_code='8765AB yay'))
        pass

    def test_defaults(self):
        self.assertEqual(self.dt_3.key_column_name, 'key')
        self.assertEqual(self.dt_3.db_table_class_name, 'local_data_storage_raw_data')

    def test_content_constraints(self):
        # Test that content is part of the correct declaration
        # cls.mc_2()
        #
        # code = StoredDataCode.objects.create(code_type=self.sdcd_2, identification_code='1962')
        #
        # # Declarations should not match and it should throw an error
        # self.assertNotClean(StoredDataContent(code=code,
        #                                       content="3",
        #                                       data_declaration=self.sdcd_1_data[0]))
        #
        # # Declarations should match and it should not throw an error
        # self.assertClean(StoredDataContent(code=code,
        #                                    content="3",
        #                                    data_declaration=self.sdcd_2_data[0]))
        pass
