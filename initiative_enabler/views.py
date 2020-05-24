from django.views.generic import FormView, ListView, CreateView, UpdateView, DetailView, View, TemplateView
from django.views.generic.edit import ModelFormMixin, ProcessFormView
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.contrib import messages
from django.urls import reverse, reverse_lazy

from Questionaire.models import *
from initiative_enabler.models import *
from initiative_enabler.forms import *


"""
Mixins
"""


class InquiryMixin:
    def setup(self, request, *args, **kwargs):
        self.inquirer = get_object_or_404(Inquirer, id=request.session.get('inquirer_id', None))
        self.inquiry = self.inquirer.active_inquiry
        return super(InquiryMixin, self).setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InquiryMixin, self).get_context_data(**kwargs)
        context['inquiry'] = self.inquiry
        context['inquirer'] = self.inquirer
        return context


class EditCollectiveMixin:
    """ A mixin that initialises the collective"""
    inquirer = None
    collective = None

    def dispatch(self, request, *args, **kwargs):
        self.inquirer = get_object_or_404(Inquirer, id=self.request.session.get('inquirer_id', None))
        self.collective = get_object_or_404(InitiatedCollective, id=kwargs['collective_id'])
        return super(EditCollectiveMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EditCollectiveMixin, self).get_context_data(**kwargs)
        context['collective'] = self.collective
        context['inquirer'] = self.inquirer
        return context


class QuickEditMixin:
    """ A mixin for form editing views that should not display the form on a seperate page.
    I.e. for quick adjustments elsewhere. Useful for one-click events. Process will be displayed through a succesmessage
     or the first error defined in the form """

    def get(self, request, *args, **kwargs):
        """ Redirects get requests as they can not occur """
        message = "De pagina die u probeert te bezoeken bevat geen inhoud."
        messages.add_message(request, messages.INFO, message)
        return HttpResponseRedirect(self.default_get_redirect_url())

    def default_get_redirect_url(self):
        return self.get_success_url()

    def form_valid(self, form):
        response = form.save()
        messages.add_message(self.request, *response)
        return super(QuickEditMixin, self).form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, *form.get_as_error_message())
        return HttpResponseRedirect(self.default_get_redirect_url())


class QuickEditCollectiveMixin(EditCollectiveMixin, QuickEditMixin):
    """ Redirects get requests as they can not occur """

    def get_form_kwargs(self):
        kwargs = super(QuickEditCollectiveMixin, self).get_form_kwargs()
        kwargs['collective'] = self.collective
        return kwargs

    def get_success_url(self):
        return self.collective.get_absolute_url()


"""
General back-end views
TODO: Delete or restructure them to prevent access
"""


class CollectiveOverview(InquiryMixin, ListView):
    model = TechCollective
    template_name = "initiative_enabler/collective_overview.html"
    context_object_name = "collectives"


class StartCollectiveView(InquiryMixin, FormView):
    form_class = StartCollectiveFormTwoStep
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


class CollectiveInfoView(InquiryMixin, DetailView):
    model = TechCollective
    template_name = "initiative_enabler/user_zone/collective_uninitiated_page.html"
    pk_url_kwarg = "collective_id"
    context_object_name = "tech_collective"

    def get_context_data(self, **kwargs):
        context = super(CollectiveInfoView, self).get_context_data(**kwargs)
        context['num_interested'] = self.object.get_interested_inquirers(self.inquirer).count()
        context['create_collective_form'] = StartCollectiveFormTwoStep(inquirer=self.inquirer,
                                                                       tech_collective=self.object)
        return context


class TakeActionOverview(InquiryMixin, TemplateView):
    template_name = "initiative_enabler/user_zone/take_action_overview.html"

    def get_context_data(self, **kwargs):
        context = super(TakeActionOverview, self).get_context_data(**kwargs)
        context['advised_techs'] = []

        for tech in TechGroup.objects.all():
            tech_score = tech.get_score(self.inquiry)
            if tech_score == Technology.TECH_SUCCESS:
                context['advised_techs'].append(tech)

        return context


class AdjustTechCollectiveInterestView(InquiryMixin, QuickEditMixin, FormView):
    form_class = AdjustTechCollectiveForm
    success_url = reverse_lazy('collectives:take_action')

    def setup(self, request, *args, **kwargs):
        super(AdjustTechCollectiveInterestView, self).setup(request, *args, **kwargs)
        self.tech_collective = get_object_or_404(TechCollective, id=kwargs['collective_id'])

    def get_form_kwargs(self):
        kwargs = super(AdjustTechCollectiveInterestView, self).get_form_kwargs()
        kwargs['inquirer'] = self.inquirer
        kwargs['tech_collective'] = self.tech_collective
        return kwargs

    def get_success_url(self):
        redirect_url = self.request.GET.get('redirect_to', None)
        if redirect_url:
            return redirect_url
        else:
            return super(AdjustTechCollectiveInterestView, self).get_success_url()


"""
Initiated Collective views
"""


class InitiatedCollectiveOverview(ListView):
    model = InitiatedCollective
    template_name = "initiative_enabler/active_collectives_list.html"
    context_object_name = "collectives"


def render_collective_detail(request, *args, **kwargs):
    """ Determine which view needs to be used. As owner or as follower """

    collective = get_object_or_404(InitiatedCollective, id=kwargs.get('collective_id', None))
    inquirer = get_object_or_404(Inquirer, id=request.session.get('inquirer_id', None))

    if collective.inquirer == inquirer:
        view_class = InitiatedCollectiveStarterDetailsView
    elif collective.collectiveapprovalresponse_set.filter(inquirer=inquirer).count() > 0:
        view_class = InitiatedCollectiveFollowerDetailsView
    else:
        raise Http404("Dit collectief kan niet worden gevonden of u bent niet onderdeel van dit collectief")

    return view_class.as_view()(request, *args, **kwargs)


class InitiatedCollectiveStarterDetailsView(InquiryMixin, DetailView):
    model = InitiatedCollective
    template_name = "initiative_enabler/user_zone/initiated_collective_details_starter.html"
    pk_url_kwarg = "collective_id"
    context_object_name = "collective"

    def get_context_data(self, **kwargs):
        context = super(InitiatedCollectiveStarterDetailsView, self).get_context_data()
        context['personal_data_form'] = EditPersonalDataForm(collective=context['object'], inquirer=self.inquirer)
        context['tech_collective'] = self.object.tech_collective
        return context


class InitiatedCollectiveFollowerDetailsView(InquiryMixin, DetailView):
    model = InitiatedCollective
    template_name = "initiative_enabler/user_zone/initiated_collective_details_follower.html"
    pk_url_kwarg = "collective_id"
    context_object_name = "collective"

    def get_context_data(self, **kwargs):
        context = super(InitiatedCollectiveFollowerDetailsView, self).get_context_data()
        context['accepted_rsvp'] = self.object.collectiveapprovalresponse_set.filter(inquirer=self.inquirer).first()

        return context


class ChangeCollectiveStateView(QuickEditCollectiveMixin, FormView):
    form_class = SwitchCollectiveStateForm


class AdjustPersonalData(EditCollectiveMixin, FormView):
    form_class = EditPersonalDataForm
    template_name = "initiative_enabler/user_zone/initiated_collective_adjust_personal_data.html"

    def get_form_kwargs(self):
        kwargs = super(AdjustPersonalData, self).get_form_kwargs()
        kwargs['collective'] = self.collective
        kwargs['inquirer'] = self.inquirer
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.add_message(self.request, messages.SUCCESS, "Data aangepast")
        return super(AdjustPersonalData, self).form_valid(form)

    def get_success_url(self):
        return self.collective.get_absolute_url()


"""
RSVP views handling the various possible states of a collective RSVP
"""


class SendNewInvitesView(QuickEditCollectiveMixin, FormView):
    form_class = QuickSendInvitationForm


class SendReminderRSVPsView(QuickEditCollectiveMixin, FormView):
    form_class = SendReminderForm


class CollectiveRSVPView(FormView):
    form_class = RSVPAgreeForm
    template_name = "initiative_enabler/rsvps/rsvp_collective_normal.html"
    rsvp = None

    def setup(self, request, *args, **kwargs):
        super(CollectiveRSVPView, self).setup(request, *args, **kwargs)
        """ Setup the RSVP and adjust the form class or template name accordingly if necessary """
        try:
            if kwargs.get('rsvp_slug', None):
                self.rsvp = CollectiveRSVP.objects.get(url_code=kwargs.get('rsvp_slug', None))
            elif kwargs.get('collective_id', None):
                self.rsvp = CollectiveRSVP.objects.get(
                    collective_id=kwargs.get('collective_id'),
                    inquirer_id=request.session.get('inquirer_id', None))
            else:
                raise CollectiveRSVP.DoesNotExist
        except (CollectiveRSVP.DoesNotExist, Inquirer.DoesNotExist):
            self.rsvp = None
        else:

            if self.rsvp.is_expired and self.rsvp.inquirer != request.session.get('inquirer_id', None):
                self.template_name = "initiative_enabler/rsvps/rsvp_collective_expired.html"
                self.form_class = RSVPRefreshExpirationForm
            elif not self.rsvp.collective.is_open:
                self.template_name = "initiative_enabler/rsvps/rsvp_collective_on_closed.html"
                self.form_class = RSVPOnClosedForm

    def dispatch(self, request, *args, **kwargs):
        if self.rsvp is None:
            return self.render_404()

        if self.rsvp.activated:
            # RSVP is already used and thus no actions should be able to occur
            return self.render_already_used()

        return super(CollectiveRSVPView, self).dispatch(request, *args, **kwargs)

    def render_404(self):
        self.template_name = "initiative_enabler/rsvps/rsvp_collective_404.html"

        response = self.render_to_response({})
        response.status_code = 404
        return response

    def render_already_used(self):
        self.template_name = "initiative_enabler/rsvps/rsvp_collective_already_activated.html"
        response = self.render_to_response({})
        response.status_code = 410
        return response

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
    form_class = RSVPDenyForm
    template_name = "initiative_enabler/rsvps/rsvp_collective_deny.html"
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