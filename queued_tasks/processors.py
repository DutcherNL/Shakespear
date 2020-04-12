import time
import math
from django.forms import ValidationError


class TaskProcessor:
    """ The superclass for a processed task
    Task processing is called in process()
    Initial set-up and final teardown can be controlled with the set_up and tear_down classes.
    Remember to call the superclass of set_up.
    Afterwards self.iterator (created in get_iterator) is iterated and for each entry process_iteration is called.
    In this method the main time-consuming processes should occur.
    Occassionally the task object on the database is updated with the current iteration number.
    By setting the task state to CANCELLED in another process, this process is also halted (with a possible delay)

    """
    update_gap = 500
    total_entries = None
    iterator = None

    def __init__(self, task_instance):
        self.task = task_instance

    def process(self):
        """ General processing structure, should generally not be overwitten"""
        self.set_up()

        i = 1  # A number tracker to track progress
        for iteration in self.iterator:
            self.process_iteration(iteration, i)

            if i % self.update_gap == 0:
                self.update_progress(i)
                if self.check_halted():
                    self.tear_down(i)
                    return
            i += 1

        return self.tear_down(i-1)

    def get_iterator(self):
        """ Returns the iterator used for the iterations (e.g. a queryset)"""
        pass

    def check_halted(self):
        """ Checks whether the process should be halted """
        self.task.refresh_from_db(fields=['state'])
        if self.task.state == self.task.CANCELLED:
            return True
        else:
            return False

    def set_up(self):
        """ Process set-up. Initiated and sets object attributes and instances """
        self.iterator = self.get_iterator()

    def tear_down(self, i):
        """ Final tear down, data cleaning

        :param i: The number of iterations before tear_down is called.
        :return: Should return a string containing text for the feedback attribute of the task instance
        """
        return ""

    def update_progress(self, i):
        """ Updates the progress attribute of the task instance """
        self.task.progress = f'{i} / {self.total_entries}'
        self.task.save(update_fields=['progress'])


class CSVFileIterator:
    """ An iterator for the CSV file """
    def __init__(self, file, deliminator):
        """
        Initiates the CSV file
        :param file: The opened CSV file
        :param deliminator: The character separating the sections in the csv file
        """
        self.file = file
        self.deliminator = deliminator

    def __iter__(self):
        # Object itself is an iterator, so return itself
        return self

    def __next__(self):
        """
        Returns a new read line from a file and interprets the data as if it was a CSV file
        :return: The line from the CSV file in list form
        """
        line = self.file.readline()
        # If line is empty, end of document is reached
        if len(line) == 0:
            raise StopIteration

        # Decode to human readable
        line = line.decode("utf-8")
        if line.endswith('\r\n'):
            # Remove the last two newline characters
            line = line[0:-2]

        # Break up the entries
        fields = line.split(self.deliminator)
        return fields


class CSVDataUploadProcessor(TaskProcessor):
    file = None
    header_names = None
    DataModel = None

    def get_iterator(self):
        # Load the CSV file and hand it to the iterator
        file = self.task.csv_file.open()
        file.seek(0, 0)
        return CSVFileIterator(file, self.task.deliminator)

    def set_up(self):
        # Store the number of lines in the CSV
        with self.task.csv_file.open() as f:
            self.total_entries = sum(1 for line in f) - 1  # exclude header line
            # A counter to display the progress
            self.update_gap = math.ceil(math.pow(self.total_entries, 1 / 3))

        # Call the super that sets the iterator
        super(CSVDataUploadProcessor, self).set_up()

        # The first row, which are the column headers
        self.header_names = self.deconstruct_header(next(self.iterator))
        self.DataModel = self.task.data_table.get_data_class()

    def tear_down(self, i):
        return f'Processed and stored {i}/{self.total_entries} entries.'

    def deconstruct_header(self, headers):
        """ Deconstructs the headers in the given CSV-line
        It attempts to find the data columns associated with the datafields"""

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

    def process_iteration(self, data, i):
        """ Process the iteration by using the csv line data and creating/updating the content instance"""
        entry_kwargs = dict(zip(self.header_names, data))

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
