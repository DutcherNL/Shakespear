from django.db import models
from string import Formatter

from DataStorage.models import StoredDataCodeDeclaration, StoredDataDeclaration, StoredDataContent

from .base_models import Question, InquiryQuestionAnswer
from .tech_scoring_models import Score


class ExternalQuestionSource(models.Model):
    """ Inserts answers on questions from external locations"""
    question = models.OneToOneField(Question, on_delete=models.CASCADE)
    code_type = models.ForeignKey(StoredDataCodeDeclaration, on_delete=models.CASCADE)
    content_type = models.ForeignKey(StoredDataDeclaration, on_delete=models.CASCADE)
    code_source = models.CharField(max_length=256)

    def get_code(self, inquiry=None):
        """ Gets the row identifier (i.e. first column) that the data needs to use.

        :param inquiry: Inquiry model of the current inquiry
        :return: The code that specefies the data
        """
        # Analyse the code source to determine where the source needs to be obtained
        formatter = Formatter()
        iter_obj = formatter.parse(self.code_source)
        keys = []
        for literal, key, format, conversion in iter_obj:
            keys.append(key)

        format_dict = {}

        try:
            for key in keys:
                if key is None:
                    continue

                if key.startswith('q_'):
                    iqa_obj = InquiryQuestionAnswer.objects.get(question__name=key[2:], inquiry=inquiry)
                    format_dict[key] = iqa_obj.get_readable_answer()
                elif key.startswith('v_'):
                    score_obj = Score.objects.get(declaration__name=key[2:], inquiry=inquiry)
                    format_dict[key] = score_obj.score

            return self.code_source.format(**format_dict)
        except InquiryQuestionAnswer.DoesNotExist:
            return None
        except Score.DoesNotExist:
            return None

    def get_content(self, inquiry=None):
        """ Returns the given content as queried

        :param inquiry: Inquiry model of the current inquiry
        :return:
        """
        code = self.get_code(inquiry=inquiry)
        if code is None:
            return None

        try:
            return StoredDataContent.objects.get(code__identification_code=code,
                                                 code__code_type=self.code_type,
                                                 data_declaration=self.content_type).content
        except StoredDataContent.DoesNotExist:
            return None