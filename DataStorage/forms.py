from django import forms

from .models import StoredDataCode, StoredDataDeclaration, StoredDataCodeDeclaration, StoredDataContent


class DataLookupForm(forms.Form):
    data_type = forms.ModelChoiceField(queryset=StoredDataCodeDeclaration.objects.all())
    content_type = forms.ModelChoiceField(queryset=StoredDataDeclaration.objects.all())
    code = forms.CharField(max_length=64)

    @property
    def get_data(self):
        if not self.is_valid():
            return None

        keys = self.cleaned_data.keys()
        if      'code' not in keys and\
                'data_type' not in keys and\
                'content_type' not in keys:
            return None

        return StoredDataContent.objects.get(code__code_type=self.cleaned_data['data_type'],
                                             code__identification_code=self.cleaned_data['code'],
                                             data_declaration=self.cleaned_data['content_type'])

    def clean(self):
        cleaned_data = super(DataLookupForm, self).clean()

        if not (cleaned_data.get('code')):
            return cleaned_data

        if not StoredDataCode.objects.filter(identification_code=cleaned_data['code'],
                                             code_type=cleaned_data['data_type']).exists():
            raise forms.ValidationError("The given code does not match")

        if not StoredDataContent.objects.filter(code__code_type=cleaned_data['data_type'],
                                                code__identification_code=cleaned_data['code'],
                                                data_declaration=cleaned_data['content_type']).exists():
            raise forms.ValidationError(
                "The given code has no information on {0}".format(cleaned_data['content_type']))


        return cleaned_data
