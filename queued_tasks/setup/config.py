from django.urls import path, include


from shakespeare_setup.config import SetupConfig
from . import views


class SetupTasks(SetupConfig):
    name = "Queued server commands"
    url_keyword = 'server-commands'
    namespace = 'queued_tasks'
    access_required_permissions = ['queued_tasks.view_queuedtask']

    button = {
        'class': 'btn-info',
        'image': 'img/queued_tasks/setup/task-icon.svg'
    }

    def get_urls(self):
        """ Builds a list of urls """
        return [
            path('', self.limit_access(views.QueuedTaskListView.as_view()), name='home'),
        ]
