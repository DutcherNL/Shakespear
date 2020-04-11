from django import forms
from django.forms import ValidationError

from .models import DataTable, DataColumn, DataContent


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


class DataUploadForm(forms.Form):
    """
    A form that allows for data to be uploaded to a database from CSV files
    """
    csv_file = forms.FileField(required=True)
    deliminator = forms.CharField(max_length=1, initial=',')
    overwrite_with_empty = forms.BooleanField(initial=True,
                                              required=False,
                                              label="Overwrite for empty data",
                                              help_text="When your data contains gaps, should it clear the existing data with the empty data."
                                                        "This option increases processing time when disabled")

    def __init__(self, *args, data_table=None, **kwargs):
        assert data_table is not None
        self.data_table = data_table
        self.DataModel = data_table.get_data_class()
        super(DataUploadForm, self).__init__(*args, **kwargs)

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']

        if csv_file is None:
            return None

        if not csv_file.name.endswith('.csv'):
            raise ValidationError("File is not a csv")

        return csv_file

    def process_csv_file(self, commit=True):
        """
        Processes the csv file and stores all data in that CSV file
        :return: A list of any possible entries that had an incorrect code
        """

        # Get the CSV file instance ready for processing
        file = self.cleaned_data['csv_file']
        file.seek(0, 0)
        deliminator = self.cleaned_data['deliminator']
        if file is None:
            return

        # ############### ANALYSE THE HEADER COLUMNS ############# #

        # Set up veriables
        column_keys = []  # A list of all the field names in order of appearance
        data_columns = self.data_table.datacolumn_set.all()  # A queryset of all data columns
        db_key_column_name = self.data_table.db_key_column_name  # The name of the key column
        key_detected = False  # Whether the key was detected in the file
        overwrite_with_empty = self.cleaned_data['overwrite_with_empty']

        # The first row, which are the column headers
        headers = read_as_csv(file, deliminator=deliminator)

        # Loop over all columns in the header and determine what database column they represent
        for entry in headers:
            if entry == self.data_table.key_column_name or entry == "key":
                column_keys.append(db_key_column_name)
                key_detected = True
            else:
                column_name = None
                for column in data_columns:
                    if entry == column.name:
                        column_name = column._db_column_name
                        break
                if column_name:
                    column_keys.append(column_name)
                else:
                    raise KeyError(f"Column '{entry}' not associated with database table")

        if not key_detected:
            raise KeyError(f"File did not contain the column key name '{self.data_table.key_column_name}'. "
                           f"Ensure that is in the file or a column is named 'key'")

        # ############### PROCESS ALL ENTRIES ############# #

        # Read all the data in the file
        if commit:
            data = read_as_csv(file, deliminator=deliminator)

            while data is not None:
                # Zip the data and column names
                entry_kwargs = dict(zip(column_keys, data))

                # Remove all empty values if required
                if not overwrite_with_empty:
                    replace_dict = {}
                    for key, item in entry_kwargs.items():
                        if item is not None and item != '':
                            replace_dict[key] = item
                    entry_kwargs = replace_dict

                # Create the instance and validate it
                data_entry = self.DataModel(**entry_kwargs)
                try:
                    data_entry.clean_fields()
                    data_entry.clean()
                except ValidationError as validation_error:
                    print(f'raised error: {validation_error.message}')
                else:
                    # The model is valid except for possibly uniqueness.
                    # The only parameter that has to be unique is the key, which we will adress here as we need to
                    # overwrite any similar entry.
                    key = entry_kwargs.pop(db_key_column_name)
                    num_adjusted = self.DataModel.objects.filter(**{db_key_column_name: key}).update(**entry_kwargs)
                    if num_adjusted == 0:
                        data_entry.save()

                # Read the next line and loop
                data = read_as_csv(file, deliminator=deliminator)

        return None


class FilterDataForm(forms.Form):
    search_data = {}
    search_query_filters = {}

    def __init__(self, *args, data_table=None, **kwargs):
        assert data_table is not None
        self.data_table = data_table
        super(FilterDataForm, self).__init__(*args, **kwargs)
        self.create_fields()
        self.set_up_filter_data()

    def get_as_field_name(self, name):
        return 'filter__'+str(name)

    def create_fields(self):
        """ Create the local form fields from the datatable instance """
        data_table_obj = self.data_table

        # Set the model key field
        self.key_field_name = self.get_as_field_name(data_table_obj.db_key_column_name)
        self.fields[self.key_field_name] = forms.CharField(required=False)
        # Set the other property fields
        for column in data_table_obj.datacolumn_set.all():
            self.fields[self.get_as_field_name(column.db_column_name)] = forms.CharField(required=False)

    def set_up_filter_data(self):
        """ Sets up the data the needs to be filtered """
        for key, item in self.data.items():
            if key.startswith('filter__'):
                if item is not None and item != "":
                    self.search_query_filters[key[8:] + '__icontains'] = item
                    self.search_data[key] = item

    def filter(self, queryset):
        return queryset.filter(**self.search_query_filters)

    @property
    def filter_url_kwargs(self):
        url = ""
        for key, value in self.search_data.items():
            url += f'{key}={value}&'

        print(f'URL {url}')

        return url




