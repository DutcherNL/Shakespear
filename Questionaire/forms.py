from django import forms
from .models import PageEntry, Inquiry

from .fields import FieldFactory, QuestionFieldMixin
from .widgets import IgnorableInput


class QuestionPageForm(forms.Form):
    """
    The Form presenting all questions on a page
    """

    def __init__(self, page, inquiry, *args, **kwargs):
        super(QuestionPageForm, self).__init__(*args, **kwargs)
        self.page = page

        for entry in PageEntry.objects.filter(page=page).order_by('position'):
            field = FieldFactory.get_field_by_entrymodel(entry, inquiry=inquiry)
            if isinstance(field, QuestionFieldMixin):
                field.backward(inquiry)

            self.fields[field.name] = field

    def save(self, inquiry):

        if inquiry is int:
            inquiry = Inquiry.objects.get(id=inquiry)

        for key, value in self.cleaned_data.items():
            self.fields[key].save(value, inquiry)

    def forward(self, inquiry):
        """
        Compute the effects of the form, works in the assumption it is not yet completed.
        :return:
        """
        # For each question in this form
        # Process the anwers

        # Loop over all questions in this form
        for field in self.fields.values():
            field.forward(inquiry)
            pass

    def backward(self, inquiry):
        """
        Compute the effects of the form, works in the assumption it is not yet completed.
        :return:
        """
        # For each question in this form
        # Process the anwers

        # Loop over all questions in this form
        for field in self.fields.values():
            field.backward(inquiry)
            pass


class EmailForm(forms.Form):
    email = forms.EmailField(widget=IgnorableInput, required=False)

    def __init__(self, *args, inquiry=None, **kwargs):
        if inquiry is None:
            raise KeyError("inquiry is missing or is None")

        self.inquiry = inquiry

        return super(EmailForm, self).__init__(*args, **kwargs)

    def save(self):
        # TODO save email in inquiry
        pass


class InquiryLoadForm(forms.Form):
    code = forms.CharField(max_length=6)
    inquiry_model = None

    def clean(self):
        cleaned_data = super(InquiryLoadForm, self).clean()

        code = cleaned_data.get('code')

        if code is not None:
            try:
                self.inquiry_model = Inquiry.get_inquiry_model_from_code(code)
            except Inquiry.DoesNotExist:
                raise forms.ValidationError("Code is incorrect. Inquiry is not known")

        return cleaned_data

    def get_inquiry(self):
        if self.inquiry_model is None:
            raise ValueError("No inquiry model computed yet")

        return self.inquiry_model