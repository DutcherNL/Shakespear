from Questionaire.models import *


class DataTestingMixin:
    @classmethod
    def setUpTestData(cls):
        cls.sdcd_1 = StoredDataCodeDeclaration.objects.create(name='postcode', code_regex='^[0-9]{4}[A-Z]{2}$')
        cls.sdcd_1_data = []
        cls.sdcd_1_data.append(StoredDataDeclaration.objects.create(code_type=cls.sdcd_1, name='eigenschap_1'))
        cls.sdcd_1_data.append(StoredDataDeclaration.objects.create(code_type=cls.sdcd_1, name='eigenschap_2'))
        cls.sdcd_1_data.append(StoredDataDeclaration.objects.create(code_type=cls.sdcd_1, name='eigenschap_3'))

        cls.sdcd_2 = StoredDataCodeDeclaration.objects.create(name='bouwjaar',
                                                              code_regex='^((1[7-9])|20)[0-9]{2}$')
        cls.sdcd_2_data = []
        cls.sdcd_2_data.append(StoredDataDeclaration.objects.create(code_type=cls.sdcd_2, name='isolatiescore'))