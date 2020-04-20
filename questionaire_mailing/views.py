from django.views.generic import TemplateView, ListView, FormView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy

from questionaire_mailing.models import MailTask, TimedMailTask, TriggeredMailTask


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


class AddTriggeredMailView(AccessabilityMixin, CreateView):
    model = TriggeredMailTask
    success_url = reverse_lazy('setup:mailings:overview')
    template_name = "questionaire_mailing/mail_task_form.html"
    fields = ['name', 'description', 'event']


class MailTaskUpdateMixin:
    def get_object(self, queryset=None):
        model = get_object_or_404(MailTask, id=self.kwargs.get('mail_id'))
        model = model.get_as_child()
        return model


class UpdateMailTaskView(AccessabilityMixin, MailTaskUpdateMixin, UpdateView):
    success_url = reverse_lazy('setup:mailings:overview')
    template_name = "questionaire_mailing/mail_task_form.html"

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().active:
            messages.warning(request, "You can not alter settings on active tasks")
            return HttpResponseRedirect(reverse_lazy('setup:mailings:overview'))

        return super(UpdateMailTaskView, self).dispatch(request, *args, **kwargs)

    def get_form_class(self):
        if isinstance(self.object, TimedMailTask):
            # Set the fields for the TimedMailTask
            self.fields = ['name', 'description', 'days_after', 'trigger']
        elif isinstance(self.object, TriggeredMailTask):
            # Set the fields for the TimedMailTask
            self.fields = ['name', 'description', 'event']

        return super(UpdateMailTaskView, self).get_form_class()

    def form_valid(self, form):
        result = super(UpdateMailTaskView, self).form_valid(form)
        # The activate button was pressed, so activate the mail task
        if 'save-and-activate' in self.request.POST:
            form.instance.activate()
        return result


class ActivateMailTaskView(AccessabilityMixin, MailTaskUpdateMixin, UpdateView):
    success_url = reverse_lazy('setup:mailings:overview')
    template_name = "questionaire_mailing/mail_task_deactivate.html"
    fields = []

    def form_valid(self, form):
        result = super(DeactivateMailTaskView, self).form_valid(form)
        # The activate button was pressed, so activate the mail task
        form.instance.deactivate()
        return result


class DeactivateMailTaskView(AccessabilityMixin, MailTaskUpdateMixin, UpdateView):
    success_url = reverse_lazy('setup:mailings:overview')
    template_name = "questionaire_mailing/mail_task_deactivate.html"
    fields = []

    def form_valid(self, form):
        result = super(DeactivateMailTaskView, self).form_valid(form)
        # The activate button was pressed, so activate the mail task
        form.instance.deactivate()
        return result
