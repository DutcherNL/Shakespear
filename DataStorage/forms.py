from django import forms
from django.forms import ValidationError

from .models import StoredDataCode, StoredDataDeclaration, StoredDataCodeDeclaration, StoredDataContent, DataBatch


def read_as_csv(file, deliminator=';'):
    """
    Returns a new read line from a file and interprets the data as if it was a CSV file
    :param file: The CSV file
    :param deliminator: The deliminator of the csv file. Default: ;
    :return: The line from the CSV file
    """
    line = file.readline()
    # If line is empty, end of document is reached
    if len(line) == 0:
        return None

    # Decode to human readable
    line = line.decode("utf-8")
    if line.endswith('\r\n'):
        # Remove the last two newline characters
        line = line[0:-2]

    # Break up the entries
    fields = line.split(deliminator)
    return fields


class DataUploadForm(forms.ModelForm):
    """
    A form that allows for data to be uploaded to a database from CSV files
    """
    csv_file = forms.FileField(required=True)
    deliminator = forms.CharField(max_length=1, initial=',')

    class Meta:
        model = DataBatch
        exclude = ()

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']

        if csv_file is None:
            return None

        if not csv_file.name.endswith('.csv'):
            raise ValidationError("File is not a csv")

        return csv_file

    def clean(self):
        cleaned_data = super().clean()

        # Clean the file itself (uses two fields and is therefore placed here)
        file = self.cleaned_data.get('csv_file', None)
        if file is not None:
            # Decrypt headers
            headers = read_as_csv(file, deliminator=self.cleaned_data['deliminator'])
            # First entry is Code Declaration Name
            declarations = []
            try:
                declarations.append(StoredDataCodeDeclaration.objects.get(name=headers[0]))
            except StoredDataCodeDeclaration.DoesNotExist:
                raise ValidationError("The term '{data_code}' does not match any of the known data codes".
                                      format(data_code=headers[0]))

            for data_entry in headers[1:]:
                try:
                    data_decl = StoredDataDeclaration.objects.get(name=data_entry)
                    # Check if this data type is allowed
                    if data_decl.code_type != declarations[0]:
                        raise ValidationError("{data} is not part of {code}".format(data=data_decl, code=declarations[0]))
                    declarations.append(data_decl)

                except StoredDataDeclaration.DoesNotExist:
                    raise ValidationError("The term '{data_type}' does not match any of the known data types".
                                          format(data_type=repr(data_entry)))
        return cleaned_data

    def save(self, commit=True, return_with_errors=False):
        result = super(DataUploadForm, self).save(commit=commit)
        if commit:
            false_entries = self.process_csv_file()
        else:
            false_entries = None
        if return_with_errors:
            return result, false_entries
        else:
            print(false_entries)
            return result

    def process_csv_file(self, commit=True):
        """
        Processes the csv file and stores all data in that CSV file
        :return: A list of any possible entries that had an incorrect code
        """
        file = self.cleaned_data['csv_file']
        file.seek(0, 0)
        deliminator = self.cleaned_data['deliminator']
        if file is None:
            return

        # Decrypt headers
        headers = read_as_csv(file, deliminator=deliminator)
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
        batch = self.instance
        if commit:
            batch.save()

        # Read all the data in the file
        data = read_as_csv(file, deliminator=deliminator)
        faulty_codes = []
        incomplete_entries = []
        empty_entries = []

        while data is not None:
            # Create the Data code root object
            code = StoredDataCode(code_type=declarations[0], identification_code=data[0])

            # Test that the code is valid, if so, process it. Otherwise don't.
            try:
                code.full_clean()
            except ValidationError:
                # Specific model was not valid, so shall not be saved, save the specific code for the log
                faulty_codes.append(data[0])
            else:
                if commit:
                    code = StoredDataCode.objects.get_or_create(code_type=declarations[0],
                                                                identification_code=data[0])[0]
                else:
                    code = StoredDataCode(code_type=declarations[0],
                                          identification_code=data[0])

                # Create all data entries on the object
                if len(data) != len(declarations):
                    incomplete_entries.append(data[0])

                for data_entry, data_decl in zip(data[1:], declarations[1:]):
                    # If data_entry does not have content, do not save it
                    if len(data_entry) > 0:
                        if commit:
                            sdc = StoredDataContent.objects.get_or_create(code=code, data_declaration=data_decl)[0]
                            sdc.content = data_entry
                            sdc.batch = batch
                            sdc.save()
                    else:
                        empty_entries.append(data[0])

            # Read the next line and loop
            data = read_as_csv(file, deliminator=deliminator)

        # Return  errors if any error is discovered
        if len(faulty_codes + empty_entries + incomplete_entries) > 0:
            return {'faulty_codes': faulty_codes, 'empty': empty_entries, 'incomplete': incomplete_entries}

        return {'faulty_codes': faulty_codes, 'empty': empty_entries, 'incomplete': incomplete_entries}
