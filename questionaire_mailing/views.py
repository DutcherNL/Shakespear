from django.views.generic import TemplateView, ListView, FormView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy

from questionaire_mailing.models import MailTask, TimedMailTask


class AccessabilityMixin(LoginRequiredMixin):
    """ A united mixin that applies for all the reports set-up views
    It is done like this because it makes changing accessiblity (future implementation of permissions) easeier
    """
    pass


class MailSetupOverview(AccessabilityMixin, ListView):
    template_name = "questionaire_mailing/mail_tasks_overview.html"
    context_object_name = "mails"
    model = MailTask


class AddTimedMailView(AccessabilityMixin, CreateView):
    model = TimedMailTask
    success_url = reverse_lazy('setup:mailings:overview')
    template_name = "questionaire_mailing/mail_task_form.html"
    fields = ['name', 'days_after', 'trigger']


class UpdateMailTaskView(AccessabilityMixin, UpdateView):
    success_url = reverse_lazy('setup:mailings:overview')
    template_name = "questionaire_mailing/mail_task_form.html"

    def get_object(self, queryset=None):
        model = MailTask.objects.get(id=self.kwargs.get('mail_id'))
        model = model.get_as_child()
        return model

    def get_form_class(self):
        if isinstance(self.object, TimedMailTask):
            # Set the fields for the TimedMailTask
            self.fields = ['name', 'days_after', 'trigger']

        return super(UpdateMailTaskView, self).get_form_class()

