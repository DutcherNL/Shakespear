from django.db import models

from Questionaire.processors.replace_text_from_database import format_from_database
from Questionaire.model_files.base_models import Question
from DataStorage.models import StoredDataCodeDeclaration, StoredDataDeclaration, StoredDataContent
from local_data_storage.models import DataTable, DataColumn


class ExternalQuestionSource(models.Model):
    """ Inserts answers on questions from external locations"""
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    code_type = models.ForeignKey(StoredDataCodeDeclaration, on_delete=models.CASCADE, null=True, blank=True)
    content_type = models.ForeignKey(StoredDataDeclaration, on_delete=models.CASCADE, null=True, blank=True)
    local_table = models.ForeignKey(DataTable, on_delete=models.CASCADE, null=True, blank=True)
    local_attribute = models.ForeignKey(DataColumn, on_delete=models.CASCADE, null=True, blank=True)

    code_source = models.CharField(max_length=256)

    def get_content(self, inquiry=None):
        """ Returns the given content as queried

        :param inquiry: Inquiry model of the current inquiry
        :return:
        """
        code = format_from_database(self.code_source, inquiry=inquiry)
        if code is None:
            return None

        if not self.local_table.is_active:
            # If the table is not active, there is no database table and thus no data
            return None

        DataClass = self.local_table.get_data_class()
        try:
            data_object = DataClass.objects.get(**{self.local_table.db_key_column_name: code})
            data_object.__getattribute__(self.local_attribute.db_column_name)
        except DataClass.DoesNotExist:
            return None