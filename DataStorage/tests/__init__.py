from Questionaire.models import *


class DataTestingMixin:
    def setUp(self):
        self.sdcd_1 = StoredDataCodeDeclaration.objects.create(name='postcode', code_regex='^[0-9]{4}[A-Z]{2}$')
        self.sdcd_1_data = []
        self.sdcd_1_data.append(StoredDataDeclaration.objects.create(code_type=self.sdcd_1, name='eigenschap_1'))
        self.sdcd_1_data.append(StoredDataDeclaration.objects.create(code_type=self.sdcd_1, name='eigenschap_2'))
        self.sdcd_1_data.append(StoredDataDeclaration.objects.create(code_type=self.sdcd_1, name='eigenschap_3'))

        self.sdcd_2 = StoredDataCodeDeclaration.objects.create(name='bouwjaar',
                                                               code_regex='^((1[7-9])|20)[0-9]{2}$')
        self.sdcd_2_data = []
        self.sdcd_2_data.append(StoredDataDeclaration.objects.create(code_type=self.sdcd_2, name='isolatiescore'))