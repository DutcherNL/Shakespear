from Questionaire.models import *
from local_data_storage.models import DataTable, DataColumn


class DataTestingMixin:
    @classmethod
    def setUpTestData(cls):
        # Datatable to test data entries
        cls.dt_1 = DataTable.objects.create(name='postcode',
                                            description='Tabel met postcode',
                                            key_column_name='postcode',
                                            key_regex='^[0-9]{4}[A-Z]{2}$',)
        cls.dt_1_columns = []
        cls.dt_1_columns.append(DataColumn.objects.create(table=cls.dt_1, name='eigenschap_1'))
        cls.dt_1_columns.append(DataColumn.objects.create(table=cls.dt_1, name='eigenschap_2'))
        cls.dt_1_columns.append(DataColumn.objects.create(table=cls.dt_1, name='eigenschap_3'))
        cls.dt_1.create_table_on_db()
        cls.mc_1 = cls.dt_1.get_data_class()

        # Datatable to test column types
        cls.dt_2 = DataTable.objects.create(name='datafields',
                                            description='test specific data fields')
        cls.dt_2_c_int = DataColumn.objects.create(table=cls.dt_2, name='Int field', column_type=DataColumn.INTFIELD)
        cls.dt_2_c_chr = DataColumn.objects.create(table=cls.dt_2, name='Chr field', column_type=DataColumn.CHARFIELD)
        cls.dt_2_c_flt = DataColumn.objects.create(table=cls.dt_2, name='Flt field', column_type=DataColumn.FLOATFIELD)
        cls.dt_2.create_table_on_db()
        cls.mc_2 = cls.dt_1.get_data_class()

        # Datatable for testing unprocessed state
        cls.mc_3 = DataTable.objects.create(name='raw data',
                                            description='test raw data, is not active')
        cls.dt_3_column = DataColumn.objects.create(table=cls.dt_3, name='Just a column')