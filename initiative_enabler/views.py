import os
from urllib.parse import urlparse, urlunparse

from django.views.generic import FormView, ListView, DetailView, TemplateView
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, Http404, FileResponse, QueryDict, HttpResponse
from django.contrib import messages
from django.urls import reverse, reverse_lazy


from general.views import StepDisplayMixin
from general.mixins import AccessMixin, RedirectThroughUriOnSuccess
from Questionaire.models import *
from Questionaire.forms import EmailForm
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


class ThirdStepDisplayMixin(StepDisplayMixin):
    """ Adds a display of the the third step """
    step = 3


class QuickEditCollectiveMixin(EditCollectiveMixin, QuickEditMixin):
    """ Redirects get requests as they can not occur """

    def get_form_kwargs(self):
        kwargs = super(QuickEditCollectiveMixin, self).get_form_kwargs()
        kwargs['collective'] = self.collective
        return kwargs

    def get_success_url(self):
        return self.collective.get_absolute_url()


class CheckEmailMixin(AccessMixin):
    """ Checks whether the given inquirer has an e-mail registered, if not divert to email processing page """
    redirect_field_name = 'on_success'
    adress_issue_url = reverse_lazy('collectives:step_3_email_request')  # The url where the issue is adressed

    def check_access_condition(self):
        # Check if there is an e-mail adres connected
        has_mail = self.inquirer.email

        return has_mail and super(CheckEmailMixin, self).check_access_condition()


"""
General back-end views
"""


class CollectiveOverview(InquiryMixin, ThirdStepDisplayMixin, ListView):
    model = TechCollective
    template_name = "initiative_enabler/collective_overview.html"
    context_object_name = "collectives"


class StartCollectiveView(InquiryMixin, CheckEmailMixin, ThirdStepDisplayMixin, FormView):
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


class CollectiveInfoView(InquiryMixin, CheckEmailMixin, ThirdStepDisplayMixin, DetailView):
    model = TechCollective
    template_name = "initiative_enabler/user_zone/collective_uninitiated_page.html"
    pk_url_kwarg = "collective_id"
    context_object_name = "tech_collective"

    def get_collective_scope_as_string(self, restriction):
        """ Computes the scope """
        scope = restriction.get_as_child().get_collective_scope(self.inquirer)

        result = ''
        add_seperation = False
        for entry in scope:
            if add_seperation:
                result += ', '
            else:
                add_seperation = True
            result += entry

        return result

    def get_context_data(self, **kwargs):

        try:
            requirement_scopes = {}
            for restriction in self.object.restrictions.all():
                display_string = f'{self.get_collective_scope_as_string(restriction=restriction)}'
                requirement_scopes[restriction.public_name] = display_string

            has_requisites_in_order = True
        except InquirerDoesNotContainRestrictionValue:
            has_requisites_in_order = False


        is_interested = TechCollectiveInterest.objects.filter(
            inquirer=self.inquirer,
            tech_collective=self.object,
            is_interested=True,
        ).exists()

        return super(CollectiveInfoView, self).get_context_data(
            num_interested=self.object.get_interested_inquirers(self.inquirer).count(),
            create_collective_form=StartCollectiveFormTwoStep(inquirer=self.inquirer, tech_collective=self.object),
            is_interested=is_interested,
            has_collective_requirements_in_order=has_requisites_in_order,
            requirement_scopes=requirement_scopes
        )


def collective_instructions_pdf(request, collective_id=None):
    """ View for rendering the PDF with instructions """
    collective = get_object_or_404(TechCollective, id=collective_id)
    if collective.instructions_file:
        try:
            filepath = collective.instructions_file.path
            return FileResponse(open(filepath, 'rb'), content_type='application/pdf')
        except FileNotFoundError:
            pass
    raise Http404("Instructies konden niet gevonden worden.")


def tech_instructions_pdf(request, tech_id=None):
    """ View for rendering the PDF with instructions """
    technology = get_object_or_404(Technology, id=tech_id)
    try:
        if technology.techimprovement.instructions_file:
            try:
                filepath = technology.techimprovement.instructions_file.path
                return FileResponse(open(filepath, 'rb'), content_type='application/pdf')
            except FileNotFoundError:
                pass
    except TechImprovement.DoesNotExist:
        pass

    raise Http404("Instructies konden niet gevonden worden.")


class EmailConfirmPage(InquiryMixin, RedirectThroughUriOnSuccess, ThirdStepDisplayMixin, FormView):
    success_url = reverse_lazy('collectives:take_action')
    template_name = 'initiative_enabler/user_zone/step_3_email_confirmation.html'
    form_class = EmailForm

    def get_form_kwargs(self):
        kwargs = super(EmailConfirmPage, self).get_form_kwargs()
        kwargs['inquirer'] = self.inquirer
        return kwargs

    def form_valid(self, form):
        form.save()
        message = "Wij hebben een mail verstuur om uw e-mail te bevestigen. Check uw mail om uw e-mail te bevestigen."
        messages.info(self.request, message=message)
        return super(EmailConfirmPage, self).form_valid(form)


class TakeActionOverview(InquiryMixin, CheckEmailMixin, ThirdStepDisplayMixin, TemplateView):
    template_name = "initiative_enabler/user_zone/take_action_overview.html"

    def get_advised_techs(self):
        """ Gets and returns all advised improvements, takes into account improvmeents that should or should not appear
        """
        advised_techs = []

        for tech_improvement in TechImprovement.objects.filter(is_active=True):

            tech_score = tech_improvement.technology.get_score(self.inquiry)
            if tech_score == Technology.TECH_SUCCESS or tech_score == Technology.TECH_VARIES:
                advised_techs.append(tech_improvement.technology)

        return advised_techs

    def has_not_interested_collectives(self):
        """ Returns a boolean whether any of the advised collectives is marked as not interested """
        advised_collectives = EnableAllTechCollectiveInterestForm.get_advised_collectives(self.inquiry)

        for tech_collective in advised_collectives:
            if not TechCollectiveInterest.objects.filter(
                    inquirer=self.inquirer,
                    tech_collective=tech_collective,
                    is_interested=True).exists():
                return True
        return False

    def get_context_data(self, **kwargs):
        context = super(TakeActionOverview, self).get_context_data(**kwargs)
        context['advised_techs'] = self.get_advised_techs()
        context['has_not_interested_collectives'] = self.has_not_interested_collectives()

        return context


class CheckRequirementsMixin:
    """ A view that handles processing of the requirements set in the collectives i.e. retrieves data from the
    inquirer to answer any requested requirement or throws a view where any missing requirement value can be given """
    requirement_forms = None
    # A hidden field that signals whether the POST originates from this view
    self_submit_field_name = "sumbit_with_requirements"

    def setup(self, request, *args, **kwargs):
        super(CheckRequirementsMixin, self).setup(request, *args, **kwargs)
        self.requirement_forms = self.construct_requirement_forms()

    def construct_requirement_forms(self):
        """ Constructs a list of all requirement forms, eventually stored in self.requirement_forms """
        forms = []
        for restriction in self.get_restrictions():
            restriction = restriction.get_as_child()
            if not restriction.has_working_restriction(self.inquirer):
                if self.self_submit_field_name in self.request.POST.keys():
                    data = self.request.POST
                else:
                    data = None
                forms.append(
                    UpdateQuestionRestrictionForm(
                        data=data,
                        restriction=restriction,
                        inquirer=self.inquirer
                    ))

        return forms

    def get_restrictions(self):
        raise NotImplementedError

    def form_valid(self, form):
        if self.process_requirement_forms(form):
            req_valid = True
            for requirement_form in self.requirement_forms:
                if not requirement_form.is_valid():
                    req_valid = False
            if req_valid:
                for requirement_form in self.requirement_forms:
                    requirement_form.save()
                    pass
                return super(CheckRequirementsMixin, self).form_valid(form)
            else:
                return self.requirements_invalid()
        else:
            return super(CheckRequirementsMixin, self).form_valid(form)

    def requirements_invalid(self):
        context = self.get_context_data()
        context['requirement_forms'] = self.requirement_forms
        context['self_submit_field_name'] = self.self_submit_field_name

        return self.response_class(
            request=self.request,
            template=[self.requirement_template_name],
            context=context,
        )

    def process_requirement_forms(self, form):
        return True


class AdjustTechCollectiveInterestView(InquiryMixin, CheckRequirementsMixin, ThirdStepDisplayMixin, QuickEditMixin, FormView):
    form_class = AdjustTechCollectiveInterestForm
    success_url = reverse_lazy('collectives:take_action')
    requirement_template_name = "initiative_enabler/user_zone/interest_restrictions_update.html"

    def setup(self, request, *args, **kwargs):
        self.tech_collective = get_object_or_404(TechCollective, id=kwargs['collective_id'])
        super(AdjustTechCollectiveInterestView, self).setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AdjustTechCollectiveInterestView, self).get_context_data(**kwargs)
        context['tech_collective'] = self.tech_collective
        context['back_url'] = self.get_success_url()
        return context

    def get_restrictions(self):
        return self.tech_collective.restrictions.all()

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

    def process_requirement_forms(self, form):
        return form.cleaned_data['is_interested']


class AdjustAllTechCollectiveInterestView(InquiryMixin, CheckRequirementsMixin, ThirdStepDisplayMixin, QuickEditMixin, FormView):
    form_class = EnableAllTechCollectiveInterestForm
    success_url = reverse_lazy('collectives:take_action')
    requirement_template_name = "initiative_enabler/user_zone/interest_all_restrictions_update.html"

    def get_context_data(self, **kwargs):
        context = super(AdjustAllTechCollectiveInterestView, self).get_context_data(**kwargs)
        context['back_url'] = self.get_success_url()
        return context

    def get_form_kwargs(self):
        kwargs = super(AdjustAllTechCollectiveInterestView, self).get_form_kwargs()
        kwargs['collectives'] = EnableAllTechCollectiveInterestForm.get_advised_collectives(self.inquiry)
        kwargs['inquirer'] = self.inquirer
        return kwargs

    def get_restrictions(self):
        advised_collectives = EnableAllTechCollectiveInterestForm.get_advised_collectives(self.inquiry)
        restrictions = CollectiveRestriction.objects.filter(techcollective__in=advised_collectives)
        return restrictions


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


class InitiatedCollectiveStarterDetailsView(InquiryMixin, ThirdStepDisplayMixin, DetailView):
    model = InitiatedCollective
    template_name = "initiative_enabler/user_zone/initiated_collective_details_starter.html"
    pk_url_kwarg = "collective_id"
    context_object_name = "collective"

    def get_context_data(self, **kwargs):
        context = super(InitiatedCollectiveStarterDetailsView, self).get_context_data()
        context['personal_data_form'] = EditPersonalDataForm(collective=context['object'], inquirer=self.inquirer)
        context['tech_collective'] = self.object.tech_collective
        return context


class InitiatedCollectiveFollowerDetailsView(InquiryMixin, ThirdStepDisplayMixin, DetailView):
    model = InitiatedCollective
    template_name = "initiative_enabler/user_zone/initiated_collective_details_follower.html"
    pk_url_kwarg = "collective_id"
    context_object_name = "collective"

    def get_context_data(self, **kwargs):
        context = super(InitiatedCollectiveFollowerDetailsView, self).get_context_data()
        context['accepted_rsvp'] = self.object.collectiveapprovalresponse_set.filter(inquirer=self.inquirer).first()

        return context


class ChangeCollectiveStateView(QuickEditCollectiveMixin, ThirdStepDisplayMixin, FormView):
    form_class = SwitchCollectiveStateForm


class AdjustPersonalData(EditCollectiveMixin, ThirdStepDisplayMixin, FormView):
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

            if self.rsvp.is_expired and self.rsvp.inquirer.id != request.session.get('inquirer_id', None):
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