from django.forms import forms

from Questionaire.models import InquiryQuestionAnswer, Score


class RemoveInquiryDataForm(forms.Form):

    def __init__(self, *args, inquiry=None, **kwargs):
        assert inquiry is not None
        self.inquiry = inquiry

        super(RemoveInquiryDataForm, self).__init__(*args, **kwargs)

    def delete(self):
        # Delete all related data
        InquiryQuestionAnswer.objects.filter(
            inquiry=self.inquiry,
        ).delete()

        Score.objects.filter(
            inquiry=self.inquiry
        ).delete()

        # Todo, write test
