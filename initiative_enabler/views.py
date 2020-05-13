from django.views.generic import FormView, ListView, CreateView, UpdateView, DetailView, View
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib import messages
from django.urls import reverse

from initiative_enabler.models import *
from initiative_enabler.forms import *


class InquiryMixin:
    def dispatch(self, request, *args, **kwargs):
        self.inquirer = get_object_or_404(Inquirer, id=self.request.session.get('inquirer_id', None))
        self.inquiry = self.inquirer.active_inquiry
        return super(InquiryMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InquiryMixin, self).get_context_data(**kwargs)
        context['inquiry'] = self.inquiry
        return context


class CollectiveOverview(InquiryMixin, ListView):
    model = TechCollective
    template_name = "initiative_enabler/collective_overview.html"
    context_object_name = "collectives"


class StartCollectiveView(InquiryMixin, FormView):
    form_class = StartCollectiveForm
    template_name = "initiative_enabler/initiate_collective.html"

    def dispatch(self, request, *args, **kwargs):
        self.tech_collective = get_object_or_404(TechCollective, id=self.kwargs.get('collective_id', None))
        return super(StartCollectiveView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(StartCollectiveView, self).get_form_kwargs()
        kwargs.update({
            'inquirer': self.inquirer,
            'tech_collective': self.tech_collective
        })
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        return super(StartCollectiveView, self).form_valid(form)

    def get_success_url(self):
        return reverse('collectives:actief_collectief_details', kwargs={
            'collective_id': self.object.id
        })


class InitiatedCollectiveOverview(ListView):
    model = InitiatedCollective
    template_name = "initiative_enabler/active_collectives_list.html"
    context_object_name = "collectives"


class InitiatedCollectiveDetailsView(InquiryMixin, DetailView):
    model = InitiatedCollective
    template_name = "initiative_enabler/initiated_collective_details_starter.html"
    pk_url_kwarg = "collective_id"
    context_object_name = "collective"


class EditCollectiveMixin:
    """ A mixin that initialises the collective"""
    inquirer = None
    collective = None

    def dispatch(self, request, *args, **kwargs):
        self.inquirer = get_object_or_404(Inquirer, id=self.request.session.get('inquirer_id', None))
        self.collective = get_object_or_404(InitiatedCollective, id=kwargs['collective_id'])
        return super(EditCollectiveMixin, self).dispatch(request, *args, **kwargs)


class QuickEditCollectiveMixin(EditCollectiveMixin):
    """ Redirects get requests as they can not occur """
    def get(self, request, *args, **kwargs):
        message = "De pagina die u probeert te bezoeken bevat geen inhoud."
        messages.add_message(request, messages.INFO, message)
        return HttpResponseRedirect(self.collective.get_absolute_url())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, collective=self.collective, current_inquirer=self.inquirer)
        if form.is_valid():
            response = form.save()
        else:
            response = messages.ERROR, form.non_field_errors()[0]

        messages.add_message(request, *response)
        return HttpResponseRedirect(self.collective.get_absolute_url())


class ChangeCollectiveStateView(QuickEditCollectiveMixin, View):
    form_class = SwitchCollectiveStateForm


class SendNewInvitesView(QuickEditCollectiveMixin, View):
    form_class = SendInvitationForm


class SendReminderRSVPsView(QuickEditCollectiveMixin, View):
    form_class = SendReminderForm


class CollectiveRSVPView(FormView):
    form_class = RSVPAgreeForm
    template_name = "initiative_enabler/rsvp_collective.html"

    def dispatch(self, request, *args, **kwargs):
        try:
            self.rsvp = CollectiveRSVP.objects.get(url_code=self.kwargs.get('rsvp_slug', None))
        except CollectiveRSVP.DoesNotExist:
            return self.render_404()

        if self.rsvp.activated:
            # RSVP is already used and thus no actions should be able to occur
            return self.render_already_used()

        if self.rsvp.is_expired:
            self.ready_for_expired()
        elif not self.rsvp.collective.is_open:
            self.ready_for_closed()

        return super(CollectiveRSVPView, self).dispatch(request, *args, **kwargs)

    def render_404(self):
        self.template_name = "initiative_enabler/rsvp_collective_404.html"
        return self.render_to_response({})

    def render_already_used(self):
        self.template_name = "initiative_enabler/rsvp_collective_already_activated.html"
        return self.render_to_response({})

    def ready_for_closed(self):
        """ Set up view variables for when bouncing against a closed collective """
        self.template_name = "initiative_enabler/rsvp_collective_on_closed.html"
        self.form_class = RSVPOnClosedForm

    def ready_for_expired(self):
        """ Set up view variables for when bouncing against a closed collective """
        self.template_name = "initiative_enabler/rsvp_collective_expired.html"
        self.form_class = RSVPRefreshExpirationForm

    def get_form_kwargs(self):
        kwargs = super(CollectiveRSVPView, self).get_form_kwargs()
        kwargs.update({
            'rsvp': self.rsvp,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CollectiveRSVPView, self).get_context_data(**kwargs)
        context['rsvp'] = self.rsvp
        return context

    def form_valid(self, form):
        if self.rsvp.is_expired:
            # RSVP is expired, so create and send a new invitation
            message = form.send()
            messages.add_message(self.request, *message)

        elif self.rsvp.collective.is_open:
            self.object = form.save()
            messages.add_message(self.request, messages.SUCCESS, "U heeft de uitnodiging geaccepteerd")
        else:
            message = form.save()
            messages.add_message(self.request, *message)

        return super(CollectiveRSVPView, self).form_valid(form)

    def get_success_url(self):
        return reverse('collectives:actief_collectief_details', kwargs={
            'collective_id': self.rsvp.collective.id
        })


class CollectiveRSVPDeniedView(FormView):
    form_class = RSVPDisagreeForm
    template_name = "initiative_enabler/rsvp_collective_deny.html"
    success_template_name = "initiative_enabler/rsvp_collective_deny_succesful.html"

    def dispatch(self, request, *args, **kwargs):
        self.rsvp = get_object_or_404(CollectiveRSVP, url_code=self.kwargs.get('rsvp_slug', None))
        return super(CollectiveRSVPDeniedView, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CollectiveRSVPDeniedView, self).get_form_kwargs()
        kwargs.update({
            'rsvp': self.rsvp,
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(CollectiveRSVPDeniedView, self).get_context_data(**kwargs)
        context['rsvp'] = self.rsvp
        return context

    def form_valid(self, form):
        form.save()
        # Render
        self.template_name = self.success_template_name
        context = self.get_context_data()
        return self.render_to_response(context)

