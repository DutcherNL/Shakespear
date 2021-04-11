from django.views import View
from django.views.generic import TemplateView, CreateView, FormView, RedirectView
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from .models import Page, Inquiry, Technology, Inquirer, TechGroup
from .forms import QuestionPageForm, EmailForm, InquirerLoadForm, CreateInquirerForm

from general.views import StepDisplayMixin
from PageDisplay.views import PageInfoView
from reports.models import Report, RenderedReport
from reports.responses import StoredPDFResponse
from reports.report_plotter import ReportPlotter
from questionaire_mailing.models import TriggeredMailTask

# Create your views here.


class FlexCssMixin:
    """ A mixin that provides a couple of site wide implementations to the templateviews"""
    def dispatch(self, request, *args, **kwargs):
        # Search for a colorsheme attribute in the GET arguments and store it in the session
        colorscheme = request.GET.get('colorscheme', None)
        if colorscheme:
            if colorscheme == "reset":
                # Reset the colorscheme to the default
                del request.session['colorscheme']
            else:
                request.session['colorscheme'] = colorscheme

        return super(FlexCssMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super(FlexCssMixin, self).get_context_data(**kwargs)
        # Add the color_scheme attribute the the context arguments
        context_data['color_scheme'] = self.request.session.get('colorscheme', None)
        return context_data


class FirstStepMixin(StepDisplayMixin):
    """ Sets the first step in the display for the three step process """
    step = 1


class BaseTemplateView(FlexCssMixin, TemplateView):
    """ A special templateview that implements some site-wide common behaviour """
    pass


class ApprovePoliciesView(FlexCssMixin, FormView):
    template_name = "inquiry/inquiry_accept_policies.html"


class CreateNewInquirerView(FlexCssMixin, FormView):
    """ Creates a new inquirer object without User interaction """
    form_class = CreateInquirerForm
    template_name = "inquiry/inquiry_accept_policies.html"
    success_url = reverse_lazy('start_query')

    def get_form_kwargs(self):
        kwargs = super(CreateNewInquirerView, self).get_form_kwargs()
        if self.request.user.is_authenticated:
            kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        self.request.session['inquirer_id'] = form.instance.id
        return super(CreateNewInquirerView, self).form_valid(form)


class InquiryStartScreen(FlexCssMixin, FirstStepMixin, FormView):
    """ A webpage that start the inquiry
    It displays the unique code and asks for an e-mail adress """
    form_class = EmailForm
    template_name = "inquiry/inquiry_start.html"

    @property
    def inquirer(self):
        """ The inquirer using the current view """
        return get_object_or_404(Inquirer, id=self.request.session.get('inquirer_id', None))

    def get_form_kwargs(self):
        form_kwargs = super(InquiryStartScreen, self).get_form_kwargs()
        # Set the inquirer object
        form_kwargs['inquirer'] = self.inquirer
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super(InquiryStartScreen, self).get_context_data(**kwargs)
        context['inquirer'] = self.inquirer
        return context

    def get_success_url(self):
        # Set the page id and inquirer id in the sessions
        self.request.session['inquiry_id'] = self.inquirer.active_inquiry.id

        current_page = self.inquirer.active_inquiry.current_page
        if current_page:
            self.request.session['page_id'] = current_page.id

        return get_continue_url(self.request, self.inquirer, exclude_mail_check=True)

    def form_valid(self, form):
        # Save the form
        form.save()

        # Create the inquiry if needed
        if self.inquirer.active_inquiry is None:
            # Create the inquiry
            page = Page.objects.order_by('position').first()
            inquiry = Inquiry.objects.create(current_page=page, inquirer=self.inquirer)

            # Create a local inquierer so we can adjust it's properties
            inquirer = self.inquirer

            # Save the inquirer
            inquirer.active_inquiry = inquiry
            inquirer.save()

        return super(InquiryStartScreen, self).form_valid(form)


class InquiryContinueScreen(InquiryStartScreen):
    """ Screen that continues the inquiry
    Asks for email is no e-mail was given """
    template_name = "inquiry/inquiry_continue_with_mailrequest.html"


class QPageView(FlexCssMixin, FirstStepMixin, FormView):
    """ The view for the question pages """
    template_name = "inquiry/inquiry_questions.html"
    form_class = QuestionPageForm

    def get_form_kwargs(self):
        form_kwargs = super(QPageView, self).get_form_kwargs()
        form_kwargs.update({
            'page': self.page,
            'inquiry': self.inquiry,
        })
        return form_kwargs

    def dispatch(self, request, *args, **kwargs):
        # Initiate the basic attributes
        self.init_base_keys()

        # Check if the page can be processed for the current inquiry
        # Some pages are blocked based on certain answers
        if not self.page.is_valid_for_inquiry(self.inquiry):
            # Determine the direction of the movement
            if self.inquiry.current_page.position < self.page.position:
                return HttpResponseRedirect(self.get_redirect(True))
            else:
                return HttpResponseRedirect(self.get_redirect(False))

        # If the page should automatically be processed. This occurs when external data needs to be retrieved
        if self.page.auto_process and self.inquiry.current_page.position != self.page.position:
            auto_result = self.autoprocess()
            if auto_result is not None:
                return auto_result

        # The page should be displayed normally
        self.inquiry.set_current_page(self.page)
        return super().dispatch(request, *args, **kwargs)

    def autoprocess(self):
        """ Attempts to autoprocess a form in its entirety even though it is likely a GET request"""
        form = QuestionPageForm(self.request.GET, page=self.page, inquiry=self.inquiry)
        if form.is_valid():
            # The form is valid, the page should not be displayed visibly
            form.save(self.inquiry)

            # Determine whether the movement is forward or backward
            if self.inquiry.current_page.position < self.page.position:
                # Movement is forward
                form.forward(self.inquiry)
                return HttpResponseRedirect(self.get_redirect(get_next=True))
            else:
                # Movement is backward
                form.backward(self.inquiry)
                return HttpResponseRedirect(self.get_redirect(get_next=False))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['questionaire_form'] = context['form']
        context['current_question_page'] = self.page

        total_page_count = Page.objects.count()
        processed_pages = Page.objects.filter(position__lt=self.page.position)

        context['progress_percentage'] = int(processed_pages.count() / total_page_count * 100)

        context['has_prev_page'] = processed_pages.exists()
        context['has_next_page'] = Page.objects.filter(position__gt=self.page.position).exists()

        context['inquiry'] = self.inquiry
        context['techs'] = Technology.objects.filter(display_in_step_1_list=True)

        return context

    def init_base_keys(self):
        self.inquiry = get_object_or_404(Inquiry, id=self.request.session.get('inquiry_id', None))

        self.page = Page.objects.filter(id=self.request.session.get('page_id', None)).first()
        if self.page is None:
            self.page = self.inquiry.current_page

    def form_valid(self, form):
        # Form is valid, save it
        form.save(self.inquiry)
        if 'prev' not in self.request.POST:
            form.forward(self.inquiry)
        return super(QPageView, self).form_valid(form)

    def form_invalid(self, form):
        # Form is invalid, save it only if the movement is backwards
        if 'prev' in self.request.POST:
            # If backwards is pressed, save current state and redirect to previous page
            form.save(self.inquiry, True)
            return HttpResponseRedirect(self.get_redirect(False))

        return super(QPageView, self).form_invalid(form)

    def get_success_url(self):
        if 'prev' in self.request.POST:
            return self.get_redirect(False)
        else:
            return self.get_redirect(True)

    def get_redirect(self, get_next):
        """ Returns the next page url

        :param get_next: Whether the next page needs to be returned (defaults True)
        :return: The url
        """
        if get_next:
            page = Page.objects.filter(position__gt=self.page.position).order_by('position').first()
        else:
            page = Page.objects.filter(position__lt=self.page.position).order_by('position').last()

        if page:
            # Set the id to the correct page id
            self.request.session['page_id'] = page.id
        elif get_next:
            # There is no next page, so the end is reached; complete the inquiry
            self.inquiry.complete()
            TriggeredMailTask.trigger(TriggeredMailTask.TRIGGER_INQUIRY_COMPLETE, inquiry=self.inquiry)
            return reverse('results_display')

        return reverse('run_query')


class TechDetailsView(FlexCssMixin, PageInfoView):
    """ Displays technology information """
    def init_params(self, **kwargs):
        self.technology = get_object_or_404(Technology, id=self.kwargs['tech_id'])
        self.page = self.technology.information_page

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['technology'] = self.technology
        return context


class QuesetionHomeScreenView(BaseTemplateView):
    template_name = "inquiry/inquiry_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['inquiries'] = Inquiry.objects.all()
        context['inquiry_entry_form'] = InquirerLoadForm(exclude=["email"])

        return context


def get_continue_url(request, inquirer, exclude_mail_check=False):
    # If inquiry is complete, display the results page
    if inquirer.active_inquiry is None:
        # There is no inquiry started yet
        return reverse('start_query')

    if inquirer.active_inquiry.is_complete:
        return reverse('results_display')

    # If an inquirer already has an e-mail adres, continue where he left off
    elif inquirer.email or exclude_mail_check:
        request.session['inquiry_id'] = inquirer.active_inquiry.id
        request.session['page_id'] = inquirer.active_inquiry.current_page.id
        return reverse('run_query')
    else:
        # There is no email, urge to fill in the email
        return reverse('continue_query')


class GetInquirerView(FlexCssMixin, FormView):
    """ A view that retrieves and connects the inquirer

    It searches the given inquirer, assures it's access and then forwards to either continuing the questionnaire
    or leads to the results page

    """
    form_class = InquirerLoadForm
    template_name = "inquiry/mail_confirmation_page.html"
    inquirer = None

    def get_form_kwargs(self):
        form_kwargs = super(GetInquirerView, self).get_form_kwargs()
        form_kwargs['initial'] = self.request.GET
        return form_kwargs

    def form_valid(self, form):
        self.inquirer = form.inquirer_model
        self.request.session['inquirer_id'] = self.inquirer.id
        return super(GetInquirerView, self).form_valid(form)

    def get_success_url(self):
        return get_continue_url(self.request, self.inquirer)


class LogInInquiry(GetInquirerView):
    template_name = "inquiry/inquiry_continue_with.html"


class JumpToCurrentView(RedirectView):

    def get_redirect_url(self):
        inquirer = get_object_or_404(Inquirer, id=self.request.session.get('inquirer_id', None))

        return get_continue_url(self.request, inquirer)


# ###############################################
# #########        RESULT VIEWS        ##########
# ###############################################


class StepTwoMixin(StepDisplayMixin):
    step = 2
    enable_step_3 = True

    def init_base_keys(self):
        self.inquirer = get_object_or_404(Inquirer, id=self.request.session.get('inquirer_id', None))
        self.inquiry = self.inquirer.active_inquiry

    def dispatch(self, request, *args, **kwargs):
        self.init_base_keys()
        return super(StepTwoMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StepTwoMixin, self).get_context_data(**kwargs)
        context['inquiry'] = self.inquiry
        return context


class QuestionaireCompleteView(StepTwoMixin, BaseTemplateView):
    """ A view that displays the inquiry results """
    template_name = 'inquiry/results/inquiry_complete.html'
    enable_step_3 = True  # step should be enabled when step 2 is

    def get_context_data(self, **kwargs):
        context = super(QuestionaireCompleteView, self).get_context_data(**kwargs)

        context['techs'] = Technology.objects.filter(display_in_step_2_list=True)

        # Create lists of various technology states
        techs_recommanded = []
        techs_unknown = []
        techs_varies = []
        techs_discouraged = []

        for tech in context['techs']:
            if hasattr(tech, 'techgroup'):
                tech = tech.techgroup

            tech_score = tech.get_score(self.inquiry)
            tech.score = tech_score

            if tech_score == Technology.TECH_SUCCESS:
                techs_recommanded.append(tech)
            elif tech_score == Technology.TECH_FAIL:
                techs_discouraged.append(tech)
            elif tech_score == Technology.TECH_VARIES:
                techs_varies.append(tech)
            elif tech_score == Technology.TECH_UNKNOWN:
                techs_unknown.append(tech)

        context['techs_recommanded'] = techs_recommanded
        context['techs_discouraged'] = techs_discouraged
        context['techs_varies'] = techs_varies
        context['techs_unknown'] = techs_unknown

        context['applicable_reports'] = self.get_applicable_reports()

        return context

    def get_applicable_reports(self):
        return Report.objects.filter(is_live=True).order_by('display_order')


class QuestionaireAdvisedView(StepTwoMixin, BaseTemplateView):
    template_name = 'inquiry/results/inquiry_techs_advised.html'

    def get_context_data(self, **kwargs):
        context = super(QuestionaireAdvisedView, self).get_context_data(**kwargs)

        techs_recommanded = []

        for tech in Technology.objects.filter(display_in_step_2_list=True):
            if hasattr(tech, 'techgroup'):
                tech = tech.techgroup

            tech.score = tech.get_score(self.inquiry)
            if tech.score == Technology.TECH_SUCCESS:
                techs_recommanded.append(tech)

        context['techs_recommanded'] = techs_recommanded

        return context


class QuestionaireRejectedView(StepTwoMixin, BaseTemplateView):
    template_name = 'inquiry/results/inquiry_techs_rejected.html'

    def get_context_data(self, **kwargs):
        context = super(QuestionaireRejectedView, self).get_context_data(**kwargs)

        techs_discouraged = []

        for tech in Technology.objects.filter(display_in_step_2_list=True):
            if hasattr(tech, 'techgroup'):
                tech = tech.techgroup

            tech.score = tech.get_score(self.inquiry)
            if tech.score == Technology.TECH_FAIL:
                techs_discouraged.append(tech)

        context['techs_discouraged'] = techs_discouraged

        return context


class ResetQueryView(StepTwoMixin, BaseTemplateView):
    """ This class proposes ans handles the event that an inquiery needs to be reset.

    Reset is that all scores are returned to their base values and the first page is the active page.
    Answeres are however maintained.

    """
    template_name = "inquiry/results/inquiry_reset.html"
    step = 1
    enable_step_2 = True

    def post(self, request, *args, **kwargs):
        inquiry = get_object_or_404(Inquiry, id=self.request.session.get('inquiry_id', None))
        inquiry.reset()
        self.request.session['page_id'] = inquiry.current_page.id

        return HttpResponseRedirect(reverse('run_query'))


class DownloadReport(StepTwoMixin, BaseTemplateView):
    download_response_class = StoredPDFResponse

    def dispatch(self, request, *args, **kwargs):
        self.report = get_object_or_404(Report, slug=self.kwargs.get('report_slug', None))
        return super(DownloadReport, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """ Get the report from the database and return it in the related response class """
        if self.report.is_static:
            rendered_report = self.get_rendered_static_report()
        else:
            rendered_report = self.get_rendered_user_report()

        return self.download_response_class(
            created_report=rendered_report
        )

    def get_rendered_static_report(self):
        """ Get the static report instance, construct it if neccesary """
        rendered_report = RenderedReport.objects.filter(
            report=self.report,
            created_on__gte=self.report.last_edited
        ).order_by(
            'created_on'
        ).first()

        if rendered_report is None:
            # The file is not yet build, so build the file.
            rendered_report = ReportPlotter(report=self.report).plot_report(inquiry=None)

        return rendered_report

    def get_rendered_user_report(self):
        """ Create or get a plot of the user-specefied report """
        rendered_report = RenderedReport.objects.filter(
            report=self.report,
            inquiry=self.inquiry,
            created_on__gte=self.inquiry.completed_on
        ).order_by(
            'created_on'
        ).first()

        if rendered_report is None:
            # The file is not yet build, so build the file.
            rendered_report = ReportPlotter(report=self.report).plot_report(inquiry=self.inquiry)

        return rendered_report
