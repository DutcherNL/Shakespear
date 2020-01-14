from django.views import View
from django.views.generic import TemplateView, CreateView, FormView
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Page, Inquiry, Technology, Inquirer, TechGroup
from .forms import QuestionPageForm, EmailForm, InquirerLoadForm

from PageDisplay.views import PageInfoView

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


class BaseTemplateView(FlexCssMixin, TemplateView):
    """ A special templateview that implements some site-wide common behaviour """
    pass


class CreateNewInquirerView(FlexCssMixin, CreateView):
    """ Creates a new inquirer object without User interaction """
    model = Inquirer
    # Fields attribute should be empty, this should be an unseen webpage
    fields = []

    def get_success_url(self):
        self.request.session['inquirer_id'] = self.object.id
        return reverse('start_query')


class InquiryStartScreen(FlexCssMixin, FormView):
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
        self.request.session['page_id'] = self.inquirer.active_inquiry.current_page.id
        self.request.session['inquiry_id'] = self.inquirer.active_inquiry.id
        return reverse('run_query')

    def form_valid(self, form):
        # Save the form
        form.save()

        # Create the inquiry if needed
        if self.inquirer.active_inquiry is None:
            # Create the inquiry
            page = Page.objects.order_by('position').first()
            inquiry = Inquiry.objects.create(current_page=page)

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


class QPageView(FlexCssMixin, FormView):
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

        context['has_prev_page'] = Page.objects.filter(position__lt=self.page.position).exists()
        context['has_next_page'] = Page.objects.filter(position__gt=self.page.position).exists()

        context['inquiry'] = self.inquiry
        context['techs'] = TechGroup.objects.all()

        return context

    def init_base_keys(self):
        self.inquiry = get_object_or_404(Inquiry, id=self.request.session.get('inquiry_id', None))
        self.page = get_object_or_404(Page, id=self.request.session.get('page_id', None))

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
        # If inquiry is complete, display the results page
        if self.inquirer.active_inquiry.is_complete:
            return reverse('results_display')

        # If an inquirer already has an e-mail adres, continue where he left off
        elif self.inquirer.email:
            self.request.session['inquiry_id'] = self.inquirer.active_inquiry.id
            self.request.session['page_id'] = self.inquirer.active_inquiry.current_page.id
            return reverse('run_query')
        else:
            # There is no email, urge to fill in the email
            return reverse('continue_query')


class LogInInquiry(GetInquirerView):
    template_name = "inquiry/inquiry_continue_with.html"


class QuestionaireCompleteView(BaseTemplateView):
    """ A view that displays the inquiry results """
    template_name = 'inquiry/inquiry_complete.html'

    def init_base_keys(self):
        self.inquirer = get_object_or_404(Inquirer, id=self.request.session.get('inquirer_id', None))
        self.inquiry = self.inquirer.active_inquiry

    def dispatch(self, request, *args, **kwargs):
        self.init_base_keys()
        return super(QuestionaireCompleteView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(QuestionaireCompleteView, self).get_context_data(**kwargs)

        context['inquiry'] = self.inquiry
        context['techs'] = TechGroup.objects.all()

        # Create lists of various technology states
        techs_recommanded = []
        techs_unknown = []
        techs_varies = []
        techs_discouraged = []

        for tech in TechGroup.objects.all():
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

        return context


class ResetQueryView(BaseTemplateView):
    """ This class proposes ans handles the event that an inquiery needs to be reset.

    Reset is that all scores are returned to their base values and the first page is the active page.
    Answeres are however maintained.

    """
    template_name = "inquiry/inquiry_reset.html"

    def post(self, request, *args, **kwargs):
        inquiry = get_object_or_404(Inquiry, id=self.request.session.get('inquiry_id', None))
        inquiry.reset()
        self.request.session['page_id'] = inquiry.current_page.id

        return HttpResponseRedirect(reverse('run_query'))







