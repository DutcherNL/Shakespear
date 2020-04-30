from local_data_storage.models import DataTable, DataColumn
from django.core.exceptions import ValidationError


class DataTestingMixin:
    @classmethod
    def define_test_tables(cls):
        """
        Sets up the Testing Data
        Note that it will raise a warning that a model is reloaded. This should not be a problem as the contents
        on the database can not change after migration. Thus no inconsistencies should be able to occur
        :return:
        """
        # Datatable to test data entries
        cls.dt_1 = DataTable.objects.create(name='postcode',
                                            description='Tabel met postcode',
                                            key_column_name='de postcode',
                                            key_regex='^[0-9]{4}[A-Z]{2}$',)
        cls.dt_1_columns = []
        cls.dt_1_columns.append(DataColumn.objects.create(table=cls.dt_1, name='eigenschap_1'))
        cls.dt_1_columns.append(DataColumn.objects.create(table=cls.dt_1, name='eigenschap_2'))
        cls.dt_1_columns.append(DataColumn.objects.create(table=cls.dt_1, name='eigenschap_3'))
        cls.PostCodeContent = cls.dt_1.get_data_class()

        # Datatable to test column types
        cls.dt_2 = DataTable.objects.create(name='data fields',
                                            description='test specific data fields')
        cls.dt_2_c_int = DataColumn.objects.create(table=cls.dt_2, name='Int field', column_type=DataColumn.INTFIELD)
        cls.dt_2_c_chr = DataColumn.objects.create(table=cls.dt_2, name='Chr field', column_type=DataColumn.CHARFIELD)
        cls.dt_2_c_flt = DataColumn.objects.create(table=cls.dt_2, name='Flt field', column_type=DataColumn.FLOATFIELD)
        cls.DataFieldContent = cls.dt_2.get_data_class()

        # Datatable for testing unprocessed state
        cls.dt_3 = DataTable.objects.create(name='raw data',
                                            description='test raw data, is not active')
        cls.dt_3_column = DataColumn.objects.create(table=cls.dt_3, name='Just a column')

    @classmethod
    def empty_data_tables(cls):
        # Remove
        DataTable.objects.all().delete()
        DataColumn.objects.all().delete()


class DataContentTestMixin(DataTestingMixin):

    @classmethod
    def setUpClass(cls):

        cls.define_test_tables()
        cls.dt_1.create_table_on_db()
        cls.dt_2.create_table_on_db()

        # Set up the rest. It enters automic in here, so the database tables must created before
        # atomic runs don't allow table creation and subsequent altering of that data table
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        # Teardown in super to end automic function
        super().tearDownClass()

        # Destroy the tables to ensure that there will be no conflict through other test classes
        cls.dt_1.destroy_table_on_db()
        cls.dt_2.destroy_table_on_db()


class ModelCleaningMixin:
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
