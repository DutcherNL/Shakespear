from django.core.management.base import BaseCommand

from queued_tasks.models import QueuedTask


class Command(BaseCommand):
    help = 'Starts an automated processing script for queued tasks'
    process_limit = 1

    def add_arguments(self, parser):
        # Named (optional) arguments
        pass

    def handle(self, *args, **options):
        # If not all maximum running tasks, activate a task in the queue
        currently_processing = QueuedTask.objects.filter(state=QueuedTask.PROCESSING).count()
        if currently_processing < self.process_limit:
            # Get the next task, if there is one, and activate it
            next_task = QueuedTask.objects.filter(state=QueuedTask.QUEUED).first()
            if next_task:
                print(f"Activating task {next_task.id}")
                next_task.get_as_child().activate()
            else:
                print("No task availlable")
        else:
            print("Limit exceeded")
