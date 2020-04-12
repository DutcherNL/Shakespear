from django.db import models
from django.utils import timezone

from queued_tasks.processors import TaskProcessor, CSVDataUploadProcessor
from local_data_storage.models import DataTable


class QueuedTask(models.Model):
    added_on = models.DateTimeField(auto_now_add=True)
    SUCCESS = 2
    PROCESSING = 1
    QUEUED = 0
    FAILED = -1
    CANCELLED = -2
    state = models.IntegerField(choices=[
        (SUCCESS, 'Success'),
        (PROCESSING, 'Processing'),
        (QUEUED, 'In queue'),
        (FAILED, 'Failed'),
        (CANCELLED, "Cancelled"),
    ], default=QUEUED)

    completed_on = models.DateTimeField(blank=True, null=True)
    progress = models.CharField(max_length=64, default="", blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)

    processor = TaskProcessor

    def activate(self):
        self.state = self.PROCESSING
        self.completed_on = timezone.now()
        self.progress = 0
        self.save()
        try:
            feedback = self.run_task()
        except Exception as e:
            self.complete(f'An exception occured: {str(e)}', succesful=False)
        else:
            self.complete(feedback, succesful=True)

    def complete(self, errors, succesful=True):
        """ Set this task as activated"""
        self.progress = None
        self.state = self.SUCCESS if succesful else self.FAILED
        self.completed_on = timezone.now()
        if errors:
            self.feedback = errors
        self.save()

    def run_task(self):
        return self.processor(self).process()

    def get_as_child(self):
        """ Returns the child object of this class"""
        # Loop over all children
        for child in self.__class__.__subclasses__():
            # If the child object exists
            if child.objects.filter(id=self.id).exists():
                return child.objects.get(id=self.id).get_as_child()
        return self

    def __str__(self):
        return self.get_as_child().__str__()


class QueuedCSVDataProcessingTask(QueuedTask):
    csv_file = models.FileField(blank=True, null=True)
    data_table = models.ForeignKey(DataTable, on_delete=models.CASCADE)
    overwrite_with_empty = models.BooleanField(default=False)
    deliminator = models.CharField(max_length=1, default=';')

    processor = CSVDataUploadProcessor

    def __str__(self):
        return f"CSV upload to {self.data_table}"





