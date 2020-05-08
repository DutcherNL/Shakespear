from django.views.generic import FormView, ListView, CreateView, UpdateView, DetailView, View
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib import messages
from django.urls import reverse

from initiative_enabler.models import *
from initiative_enabler.forms import StartCollectiveForm, RSVPAgreeForm, RSVPDisagreeForm


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


class OpenOrCloseCollectiveBaseMixin(InquiryMixin):
    collective = None

    def get(self, request, *args, **kwargs):
        self.collective = get_object_or_404(InitiatedCollective, id=self.kwargs.get('collective_id'))
        return HttpResponseRedirect(self.collective.get_absolute_url())

    def post(self, request, *args, **kwargs):
        self.collective = get_object_or_404(InitiatedCollective, id=self.kwargs.get('collective_id'))
        # if self.inquirer.id != self.collective.inquirer:
        #     return HttpResponseForbidden("You are not the owner of this initiative and can not change it")

        if self.collective.is_open != self.to_state:
            self.collective.is_open = self.to_state
            self.collective.save()
            messages.add_message(request, messages.SUCCESS, self.success_message)
        return HttpResponseRedirect(self.collective.get_absolute_url())


class CloseCollectiveView(OpenOrCloseCollectiveBaseMixin, View):
    to_state = False
    success_message = "Collectief toegang is nu geblokkeerd"


class OpenCollectiveView(OpenOrCloseCollectiveBaseMixin, View):
    to_state = True
    success_message = "Collectief toegang is nu geopend"


class CollectiveRSVPView(FormView):
    form_class = RSVPAgreeForm
    template_name = "initiative_enabler/rsvp_collective.html"

    def dispatch(self, request, *args, **kwargs):
        self.rsvp = get_object_or_404(CollectiveRSVP, url_code=self.kwargs.get('rsvp_slug', None))
        return super(CollectiveRSVPView, self).dispatch(request, *args, **kwargs)

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
        self.object = form.save()
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

