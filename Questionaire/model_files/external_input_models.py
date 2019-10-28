from django.db import models

from Questionaire.processors.replace_text_from_database import format_from_database
from Questionaire.model_files.base_models import Question
from DataStorage.models import StoredDataCodeDeclaration, StoredDataDeclaration, StoredDataContent


class ExternalQuestionSource(models.Model):
    """ Inserts answers on questions from external locations"""
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    code_type = models.ForeignKey(StoredDataCodeDeclaration, on_delete=models.CASCADE)
    content_type = models.ForeignKey(StoredDataDeclaration, on_delete=models.CASCADE)
    code_source = models.CharField(max_length=256)

    def get_content(self, inquiry=None):
        """ Returns the given content as queried

        :param inquiry: Inquiry model of the current inquiry
        :return:
        """
        code = format_from_database(self.code_source, inquiry=inquiry)
        if code is None:
            return None

        try:
            return StoredDataContent.objects.get(code__identification_code=code,
                                                 code__code_type=self.code_type,
                                                 data_declaration=self.content_type).content
        except StoredDataContent.DoesNotExist:
            return None