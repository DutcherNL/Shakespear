from django.test import TestCase, TransactionTestCase
from django.db import OperationalError, IntegrityError
from django.db.models import IntegerField, FloatField, CharField
from django.forms import ValidationError

from local_data_storage.models import DataTable, DataColumn, DataContent
from . import DataTestingMixin, ModelCleaningMixin, DataContentTestMixin

# Create your tests here.


class DataTableTestCase(DataTestingMixin, ModelCleaningMixin, TransactionTestCase):
    """
    Tests all migration and settings for the DataTable class.
    This includes:
    ensure that creation and deletion works
    ensure that vital information can not be changed when table is active (i.e. present on the database)
    ensure that the key column name and datatable name are stored correctly.
    """
    def test_defaults(self):
        """ Test the default values """
        self.define_test_tables()
        self.assertEqual(self.dt_3.key_column_name, 'key')
        self.assertEqual(self.dt_3.db_table_class_name, 'raw_data')
        self.assertFalse(self.dt_3.is_active)

        # Empty the test tables to prevent duplicates
        self.empty_data_tables()

    def test_database_migration(self):
        """
        Assert that database migration during runtime can be done correctly. Tables can't get double created or
        destroyed.
        :return:
        """
        self.define_test_tables()

        self.assertFalse(self.dt_1.is_active)
        try:
            self.dt_1.create_table_on_db()
        except OperationalError as e:
            raise AssertionError(f'An operational error occured: {str(e.value)}')

        self.assertTrue(self.dt_1.is_active)
        try:
            self.dt_1.create_table_on_db()
        except RuntimeError:
            # It should raise a runtime error as the table is already active and can not be created again
            pass
        else:
            raise AssertionError("Creating an active table should throw a RunTimeError. It didn't")

        try:
            self.dt_1.destroy_table_on_db()
        except OperationalError as e:
            raise AssertionError(f'An operational error occured: {str(e.value)}')
        self.assertFalse(self.dt_1.is_active)

        try:
            self.dt_1.destroy_table_on_db()
        except RuntimeError:
            # It should raise a runtime error as the table is not active and can not be destroyed
            pass
        else:
            raise AssertionError("Destroying an inactive table should throw a RunTimeError. It didn't")

        # Do one more run to ensure that the destory table didn't actually break something
        try:
            self.dt_1.create_table_on_db()
            self.dt_1.destroy_table_on_db()
        except OperationalError as e:
            raise AssertionError(f'An operational error occured: {str(e.value)}')

        # Empty the test tables to prevent duplicates
        self.empty_data_tables()

    def test_database_table_data(self):
        """ Test whether initiating two or more datatables don't use the same datatable """
        # Ensure that the name field is set as unique
        self.assertTrue(DataTable._meta.get_field('name').unique)

        # Ensure that entries do not conflict with each other
        self.define_test_tables()
        self.dt_1.create_table_on_db()
        self.dt_2.create_table_on_db()

        # Make sure the db table names are derived from the table name
        self.assertEqual(self.dt_1._db_table_class_name, 'postcode')
        self.assertEqual(self.dt_2._db_table_class_name, 'data_fields')

        # Ensure the key column names are correctly named
        self.assertEqual(self.dt_1._db_key_column_name, 'de_postcode')
        self.assertEqual(self.dt_2._db_key_column_name, 'key')  # It is not given, so should default to this

        self.dt_1.destroy_table_on_db()
        self.dt_2.destroy_table_on_db()
        # If all goes well, this should throw no errors and thus succeed.

        # Empty the test tables to prevent duplicates
        self.empty_data_tables()

    def test_block_db_names_adjustment_when_active(self):
        """ Tests if database table related names can NOT be adjusted, but others can """
        table = DataTable.objects.create(
            is_active=True,
            name='Test name',
            key_column_name='Key column',
            _db_table_class_name='test_db_name',
            _db_key_column_name='test_cl_name'
        )

        # Ensure that the slug is updated
        self.assertEqual(table.slug, 'test-name')

        # Try to adjust the name
        table.name = 'New name'
        table.key_column_name = 'New key column'
        table._db_table_class_name = 'false_table_name'
        table._db_table_class_name = 'false_table_name'
        table._db_key_column_name = 'false_cl_name'
        table.save()

        # Refresh from db to ensure the db state is tested instead of the cached (incorrect) version
        table.refresh_from_db()

        # It should be possible to adjust some non-db related names
        self.assertEqual(table.name, 'New name')
        self.assertEqual(table.slug, 'new-name')
        self.assertEqual(table.key_column_name, 'New key column')
        # It should not be possible to adjust db-related names after migration
        self.assertEqual(table._db_table_class_name, 'test_db_name')
        self.assertEqual(table._db_key_column_name, 'test_cl_name')

        # Test if the local property samples the correct value (i.e. the _db value and not the adjusted name)
        self.assertEqual(table.db_table_class_name, 'test_db_name')
        self.assertEqual(table.db_key_column_name, 'test_cl_name')

        # Empty the test tables to prevent duplicates
        self.empty_data_tables()


class DataColumnTestCase(DataTestingMixin, ModelCleaningMixin, TransactionTestCase):

    def test_defaults(self):
        self.define_test_tables()
        self.assertEqual(self.dt_3_column.slug, 'just-a-column')
        self.assertEqual(self.dt_3_column.column_type, DataColumn.CHARFIELD)
        self.empty_data_tables()

    def test_block_db_names_adjustment_when_active(self):
        """ Assert that, when database table is activated, database related values can not be changed """
        self.empty_data_tables()
        self.define_test_tables()

        # Set the _db_column name to a set value, as this test does not use the migrate functionality
        col_1 = self.dt_1_columns[0]
        col_1._db_column_name = 'db_prop_1'
        col_1.save()

        self.dt_1.is_active = True
        self.dt_1.save()

        col_1.refresh_from_db()
        # Check that the column has the expected values
        self.assertEqual(col_1.name, 'eigenschap_1')
        self.assertEqual(col_1._db_column_name, 'db_prop_1')
        self.assertEqual(col_1.column_type, DataColumn.CHARFIELD)

        col_1.name = 'new column name'
        col_1._db_column_name = 'waarde_1'
        col_1.column_type = DataColumn.FLOATFIELD
        col_1.save()

        # Refresh from db to ensure the db state is tested instead of the cached (incorrect) version
        col_1.refresh_from_db()

        # Check that the column has changed only the necessary values
        self.assertEqual(col_1.name, 'new column name')
        self.assertEqual(col_1.slug, 'new-column-name')
        self.assertEqual(col_1._db_column_name, 'db_prop_1')
        self.assertEqual(col_1.column_type, DataColumn.CHARFIELD)

        # Empty the test tables to prevent duplicates
        self.empty_data_tables()

    def test_column_db_types(self):
        """ Test that setting the column type results in the proper field """
        self.define_test_tables()
        self.dt_2.create_table_on_db()

        self.assertIsInstance(self.DataFieldContent._meta.get_field('int_field'), IntegerField)
        self.assertIsInstance(self.DataFieldContent._meta.get_field('chr_field'), CharField)
        self.assertIsInstance(self.DataFieldContent._meta.get_field('flt_field'), FloatField)

        self.dt_2.destroy_table_on_db()

        # Empty the test tables to prevent duplicates
        self.empty_data_tables()


class DataModelTestCase(ModelCleaningMixin, DataContentTestMixin, TestCase):
    """ Test DataModel attributes and limiations"""
    def test_content_handling(self):
        testcode_1 = self.PostCodeContent(
            key='1234AK',
            eigenschap_1='A',
            eigenschap_2='46',
            eigenschap_3='huis',
        )
        self.assertClean(testcode_1)

        # Create the entries on the database
        testcode_1.save()
        # Create a second entry to check if it works properly with multiple entries on the server
        self.PostCodeContent.objects.create(
            de_postcode='3456PL',
            eigenschap_1='Huts',
            eigenschap_2='Fijn',
            eigenschap_3='Flap',
        )

        # Check the data values
        testcode_1_check = self.PostCodeContent.objects.get(de_postcode='1234AK')
        self.assertEqual(testcode_1_check.eigenschap_1, 'A')
        self.assertEqual(testcode_1_check.eigenschap_2, '46')
        self.assertEqual(testcode_1_check.eigenschap_3, 'huis')

        # Delete the instance and check if it has been deleted
        testcode_1.delete()
        try:
            self.PostCodeContent.objects.get(de_postcode='1234AK')
        except self.PostCodeContent.DoesNotExist:
            pass
        else:
            raise AssertionError('Postocde 1234AK was not removed from datatable')

    def test_key_uniquness(self):
        self.PostCodeContent.objects.create(key='3456PL')
        try:
            self.PostCodeContent.objects.create(de_postcode='3456PL')
        except IntegrityError:
            pass
        else:
            raise AssertionError('PostCodeContent did not fail on what should be a UNIQUE Integrity error')

    def test_regex_validitiy(self):
        """ Tests that regex on the key is uphold """
        self.assertClean(self.PostCodeContent(key='1234AB'))
        self.assertClean(self.PostCodeContent(de_postcode='9999ZZ'))
        # These all should throw validation errors for non-matching regex patterns
        self.assertNotClean(  # Test incomplete validity
            self.PostCodeContent(key='1234'))
        self.assertNotClean(  # Test incorrect number of elements
            self.PostCodeContent(key='567AI'))
        self.assertNotClean(  # Test incorrect imput elements
            self.PostCodeContent(key='2589nm'))
        self.assertNotClean(  # Test start marker workings
            self.PostCodeContent(key='not 8765AB'))
        self.assertNotClean(  # Test end marker workings
            self.PostCodeContent(key='8765AB yay'))

