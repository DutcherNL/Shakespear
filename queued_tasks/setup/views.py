from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from queued_tasks.models import QueuedTask
from tools.pagination import FlexPaginationMixin


class AccessabilityMixin(LoginRequiredMixin):
    """ A united mixin that applies for all the reports set-up views
    It is done like this because it makes changing accessiblity (future implementation of permissions) easeier
    """
    pass


class QueuedTaskListView(AccessabilityMixin, FlexPaginationMixin, ListView):
    template_name = "queued_tasks/queued_tasks_overview.html"
    context_object_name = "tasks"
    model = QueuedTask
    paginate_by = 10

    def get_queryset(self):
        queryset = super(QueuedTaskListView, self).get_queryset()
        return queryset.order_by('-id')
