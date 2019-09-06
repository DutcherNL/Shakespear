from django import forms
from django.forms import ValidationError

from .models import StoredDataCode, StoredDataDeclaration, StoredDataCodeDeclaration, StoredDataContent, DataBatch


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


def read_as_csv(file, deliminator=';'):
    """
    Returns a new reaad line from a file and interprets the data as if it was a CSV file
    :param file: The CSV file
    :param deliminator: The deliminator of the csv file. Default: ;
    :return: The line from the CSV file
    """
    line = file.readline()
    # If line is empty, end of document is reached
    if len(line) == 0:
        return None

    # Decorde to human readable
    line = line.decode("utf-8")
    if line.endswith('\r\n'):
        line = line[0:-2]

    # Break up the entries
    fields = line.split(deliminator)
    return fields


class DataUploadForm(forms.Form):
    """
    A form that allows for data to be uploaded to a database from CSV files
    """
    batch_name = forms.CharField(max_length=20)
    csv_file = forms.FileField()

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            raise ValidationError("File is not a csv")
        return csv_file

    def process(self):
        file = self.cleaned_data['csv_file']
        # Decrypt headers
        headers = read_as_csv(file)
        # First entry is Code Declaration Name
        declarations = []
        try:
            declarations.append(StoredDataCodeDeclaration.objects.get(name=headers[0]))
        except StoredDataCodeDeclaration.DoesNotExist:
            raise KeyError("Code Declaration not defined properly")

        # Get the data types
        try:
            for data_entry in headers[1:]:
                data_decl = StoredDataDeclaration.objects.get(name=data_entry)
                # Check if this data type is allowed
                if data_decl.code_type != declarations[0]:
                    raise KeyError("{data} is not part of {code}".format(data=data_decl, code=declarations[0]))
                declarations.append(data_decl)

        except StoredDataDeclaration.DoesNotExist:
            raise KeyError("Data Declaration not defined properly")

        # Create a new batch identifier
        batch = DataBatch()
        batch.save()

        # Read all the data in the file
        data = read_as_csv(file)
        while data is not None:
            # Create the Data code root object
            code = StoredDataCode(code_type=declarations[0],
                                  identification_code=data[0])
            code.save()

            # Create all data entries on the object
            for data_entry, data_decl in zip(data[1:], declarations[1:]):
                StoredDataContent(code=code,
                                  data_declaration=data_decl,
                                  content=data_entry,
                                  batch=batch
                                  ).save()

            # Read the next line and loop
            data = read_as_csv(file)