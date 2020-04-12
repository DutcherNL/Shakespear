import time
import math
from django.forms import ValidationError


class TaskProcessor:
    def __init__(self, task_instance):
        self.task = task_instance

    def process(self):
        pass


class CSVDataUploadProcessor(TaskProcessor):
    counter = 500

    @staticmethod
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

    def process(self):
        """
        Processes the csv file and stores all data in that CSV file
        :return: A list of any possible entries that had an incorrect code
        """

        # Store the number of lines in the CSV
        with self.task.csv_file.open() as f:
            self.num_lines = sum(1 for line in f) - 1  # exclude header line
            # A counter to display the progress
            self.space_counter = math.ceil(math.pow(self.num_lines, 1/3))

        # Get the CSV file instance ready for processing
        file = self.task.csv_file.open()
        file.seek(0, 0)
        deliminator = self.task.deliminator
        if file is None:
            return

        # The first row, which are the column headers
        headers = self.read_as_csv(file, deliminator=deliminator)
        header_names = self.deconstruct_header(headers)

        data = self.read_as_csv(file, deliminator=deliminator)
        i = 1

        self.DataModel = self.task.data_table.get_data_class()

        while data is not None:
            self.process_entry(header_names, data)

            i += 1
            data = self.read_as_csv(file, deliminator=deliminator)

            if i % self.counter == 0:
                self.update_progress(i)

        return f'Processed and stored {self.num_lines} entries.'

    def deconstruct_header(self, headers):
        # ############### ANALYSE THE HEADER COLUMNS ############# #

        # Set up veriables
        column_keys = []  # A list of all the field names in order of appearance
        data_columns = self.task.data_table.datacolumn_set.all()  # A queryset of all data columns
        db_key_column_name = self.task.data_table.db_key_column_name  # The name of the key column
        key_detected = False  # Whether the key was detected in the file

        # Loop over all columns in the header and determine what database column they represent
        for entry in headers:
            if entry == self.task.data_table.key_column_name or entry == "key":
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

        return column_keys

    def process_entry(self, header_names, data):
        entry_kwargs = dict(zip(header_names, data))

        # Remove all empty values if required
        if not self.task.overwrite_with_empty:
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
            key = entry_kwargs.pop(self.task.data_table.db_key_column_name)
            num_adjusted = self.DataModel.objects.filter(**{self.task.data_table.db_key_column_name: key}).update(**entry_kwargs)
            if num_adjusted == 0:
                data_entry.save()

    def update_progress(self, i):
        self.task.progress = f'{i} / {self.num_lines}'
        self.task.save(update_fields=['progress'])
