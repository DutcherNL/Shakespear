import urllib
from datetime import timedelta

from django.utils import timezone
from django.db.models import Count, Q
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import Http404


from Questionaire.models import Technology, Inquirer, Inquiry
from initiative_enabler.models import TechCollective, InitiatedCollective, \
    TechCollectiveInterest, RestrictionValue, CollectiveRestriction
from .forms import *
from .models import QuestionFilter
from . import MIN_INQUIRY_REQ

from mailing.views import ConstructMailView


class AccessRestrictionMixin(PermissionRequiredMixin):
    """ A view that restricts access to only those who are authorized """
    permission_required = 'auth.can_access_data_analysis_pages'


class FilterDataMixin:
    filter_form_classes = []
    minimum_results_required = MIN_INQUIRY_REQ

    def get_context_data(self, **kwargs):
        context = super(FilterDataMixin, self).get_context_data(**kwargs)

        forms = self.get_filter_forms()
        context['forms'] = forms.values()

        context['queryset'] = self.get_queryset(forms=forms.values())
        context['MIN_INQUIRY_REQ'] = self.minimum_results_required

        # The get query parameters in url query format to be used when calling graph data
        context['query_line'] = urllib.parse.urlencode(self.request.GET)

        return context

    def get_filter_form_kwargs(self, form_class=None):
        return {}

    def get_queryset(self, forms=None):
        """ Returns the queryset of the main object analysed """
        # If no forms are given initialise local forms
        if forms is None:
            get_data = self.request.GET if self.request.GET else None
            forms = []
            for form_class in self.filter_form_classes:
                if form_class.can_filter(data=get_data, **self.get_filter_form_kwargs(form_class)):
                    form = form_class(get_data, **self.get_filter_form_kwargs(form_class))
                    forms.append(form)

        # Get the current inquiry dataset
        queryset = None
        for form in forms:
            queryset = form.get_filtered_queryset(queryset=queryset)

        return queryset

    def get_filter_forms(self):
        """ Returns a dict of all filter forms """
        get_data = self.request.GET if self.request.GET else None
        forms = {}
        for form_class in self.filter_form_classes:
            if form_class.can_filter(data=get_data, **self.get_filter_form_kwargs(form_class)):
                form = form_class(get_data, **self.get_filter_form_kwargs(form_class))
                forms[str(form.name) + ""] = form

        return forms


class InquiryDataView(AccessRestrictionMixin, FilterDataMixin, TemplateView):
    template_name = "data_analysis/data_analysis_inquiry_progress.html"
    filter_form_classes = [InquiryLastVisitedFilterForm, InquiryUserExcludeFilterForm, FilterInquiryByQuestionForm]

    def get_filter_form_kwargs(self, form_class=None):
        kwargs = super(InquiryDataView, self).get_filter_form_kwargs(form_class)
        if form_class is FilterInquiryByQuestionForm:
            kwargs.update({
                'filter_models': QuestionFilter.objects.filter(use_for_progress_analysis=True)
            })
        return kwargs


class TechDataView(AccessRestrictionMixin, FilterDataMixin, TemplateView):
    template_name = "data_analysis/data_analysis_techs.html"
    filter_form_classes = [InquiryLastVisitedFilterForm,
                           FilterInquiryByQuestionForm, InquiryUserExcludeFilterForm]

    def get_context_data(self, **kwargs):
        return super(TechDataView, self).get_context_data(
            techs=Technology.objects.all(),
            **kwargs
        )

    def get_filter_form_kwargs(self, form_class=None):
        kwargs = super(TechDataView, self).get_filter_form_kwargs(form_class)
        if form_class is FilterInquiryByQuestionForm:
            kwargs.update({
                'filter_models': QuestionFilter.objects.filter(use_for_tech_analysis=True)
            })
        return kwargs


class InterestsView(AccessRestrictionMixin, FilterDataMixin, TemplateView):
    template_name = "data_analysis/data_analysis_interests.html"
    filter_form_classes = [FilterInterestByInquirerCreationDateForm]

    def get_context_data(self, **kwargs):
        context = super(InterestsView, self).get_context_data(**kwargs)
        queryset = context['queryset']
        context['tech_collectives'] = self.get_collective_data(interests=queryset)
        return context

    def get_collective_data(self, queryset=None, interests=None):
        if queryset is None:
            queryset = TechCollective.objects.all()

        if interests is None:
            interests = TechCollectiveInterest.objects.filter(is_interested=True)
        interests = interests.filter(is_interested=True)

        queryset = queryset.annotate(collective_count=Count(
            'initiatedcollective',
            distinct=True,
        ))

        queryset = queryset.annotate(interested_count=Count(
            'techcollectiveinterest',
            filter=(
                Q(techcollectiveinterest__in=interests)
            ),
            distinct=True,
        ))

        return queryset


class TechCollectiveLookupMixin:
    collective = None

    def dispatch(self, request, *args, **kwargs):
        self.collective = get_object_or_404(TechCollective, technology__slug=self.kwargs['tech_slug'])
        return super(TechCollectiveLookupMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TechCollectiveLookupMixin, self).get_context_data(**kwargs)
        context['technology'] = self.collective.technology
        context['tech_collective'] = self.collective

        return context


class InterestDetailView(AccessRestrictionMixin, TechCollectiveLookupMixin, FilterDataMixin, TemplateView):
    template_name = "data_analysis/data_analysis_interest_detail.html"
    filter_form_classes = [FilterInterestByInquirerCreationDateForm, FilterInterestByRestrictionForm]
    minimum_results_required = 0

    def get_context_data(self, **kwargs):
        context = super(InterestDetailView, self).get_context_data(**kwargs)

        buttons = []
        for restriction in self.collective.restrictions.all():
            buttons.append({
                'text': f"Lijst {restriction.public_name}",
                'url': reverse("data_analysis:initiative_interests", kwargs={
                    'tech_slug': self.collective.technology.slug,
                    'restriction_id': restriction.id,
                }),
            })
        context['other_buttons'] = buttons

        # Restrict the results to this collective only
        context['queryset'] = context['queryset'].filter(tech_collective=self.collective)
        context['queryset_interested'] = context['queryset'].filter(is_interested=True)

        return context

    def get_filter_form_kwargs(self, form_class=None):
        kwargs = super(InterestDetailView, self).get_filter_form_kwargs(form_class)
        if form_class is FilterInterestByRestrictionForm:
            kwargs.update({
                'collective': self.collective,
            })
        return kwargs


class RestrictionMixinLookup:
    restriction = None

    def dispatch(self, request, *args, **kwargs):
        self.restriction = get_object_or_404(CollectiveRestriction, id=self.kwargs['restriction_id'])
        if not self.collective.restrictions.filter(id=self.restriction.id).exists():
            raise Http404()
        return super(RestrictionMixinLookup, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return super(RestrictionMixinLookup, self).get_context_data(
            restriction=self.restriction,
            **kwargs
        )


class InterestRestrictionListView(AccessRestrictionMixin, FilterDataMixin, TechCollectiveLookupMixin,
                                  RestrictionMixinLookup, ListView):
    """
    List view for collective interest filtered by a specific
    """
    template_name = "data_analysis/data_analysis_interest_restriction_list.html"
    filter_form_classes = [FilterInterestByInquirerCreationDateForm, FilterInterestByRestrictionForm]

    recent_days_count = 7
    minimum_results_required = 0

    # Listable attribute
    context_object_name = "restriction_list"
    paginate_by = 20
    ordering = 'value'

    def get_queryset(self, forms=None):
        queryset = super(InterestRestrictionListView, self).get_queryset(forms=forms)

        # Get all restriction values
        restriction_value_list = RestrictionValue.objects.filter(
            restriction=self.restriction,
            techcollectiveinterest__in=queryset,
        )
        # Annotate the amount of interests known for each value
        restriction_value_list = restriction_value_list. \
            annotate(total_known=Count('techcollectiveinterest', filter=
                Q(techcollectiveinterest__tech_collective=self.collective))). \
            annotate(total_interested=Count('techcollectiveinterest', filter=(
                    Q(techcollectiveinterest__is_interested=True) &
                    Q(techcollectiveinterest__tech_collective=self.collective)
        )))

        # Annotate the recent positive replies
        thresholddate = timezone.now() - timedelta(days=self.recent_days_count)
        restriction_value_list = restriction_value_list. \
            annotate(total_recent=Count(
            'techcollectiveinterest',
            filter=(
                    Q(techcollectiveinterest__last_updated__gte=thresholddate) &
                    Q(techcollectiveinterest__is_interested=True) &
                    Q(techcollectiveinterest__tech_collective=self.collective)
            )))
        return restriction_value_list.order_by('value')

    def get_context_data(self, **kwargs):
        buttons = []
        for restriction in self.collective.restrictions.all():
            buttons.append({
                'text': f"Lijst {restriction.public_name}",
                'url': reverse("data_analysis:initiative_interests", kwargs={
                    'tech_slug': self.collective.technology.slug,
                    'restriction_id': restriction.id,
                }),
            })
        # context['other_buttons'] = buttons

        return super(InterestRestrictionListView, self).get_context_data(
            recent_dayscount=self.recent_days_count,
            other_buttons=buttons,
            **kwargs)

    def get_filter_form_kwargs(self, form_class=None):
        kwargs = super(InterestRestrictionListView, self).get_filter_form_kwargs(form_class)
        if form_class is FilterInterestByRestrictionForm:
            kwargs.update({
                'collective': self.collective,
            })
        return kwargs


class SendMailToInterestedView(AccessRestrictionMixin, FilterDataMixin, TechCollectiveLookupMixin, ConstructMailView):
    template_name = "data_analysis/data_analysis_interest_mail.html"
    filter_form_classes = [FilterInterestByInquirerCreationDateForm, FilterInterestByRestrictionForm]
    form_class = InquirerMailForm

    minimum_results_required = 0

    def get_initial(self):
        initial = super(SendMailToInterestedView, self).get_initial()
        initial['to'] = "Interested inquirers"
        return initial

    def get_form_kwargs(self):
        kwargs = super(SendMailToInterestedView, self).get_form_kwargs()
        kwargs.update({
            'inquirers': self.get_inquirers()
        })
        return kwargs

    def get_filter_form_kwargs(self, form_class=None):
        kwargs = super(SendMailToInterestedView, self).get_filter_form_kwargs(form_class)
        if form_class is FilterInterestByRestrictionForm:
            kwargs.update({
                'collective': self.collective,
            })
        return kwargs

    def get_success_url(self):
        email_count = self.get_inquirers().count()
        interest_count = self.get_queryset().count()

        if email_count == 0 and interest_count > 0:
            messages.warning(
                self.request,
                f"Er zijn geen emails verzonden. Alhoewel er {interest_count} personen interesse hebben getoond "
                f"hebben zij allen niet hun email adres geverifieerd.")
        elif email_count == 0:
            messages.warning(
                self.request,
                "Er was niemand in dit filter om een mail heen te sturen.")
        else:
            message = f"Mail is succesvol naar {email_count} mensen verstuurd."
            if interest_count != email_count:
                message += f"{interest_count-email_count} mensen hebben hun email adres nog niet geverifieerd."

            messages.success(self.request, message)

        return self.request.get_full_path()
        # return reverse('data_analysis:initiative_interests', kwargs={'tech_slug': self.collective.technology.slug})

    def get_queryset(self, forms=None):
        # Adjust the queryset to only take interest people in this collective
        return super(SendMailToInterestedView, self).get_queryset(forms).\
            filter(is_interested=True).\
            filter(tech_collective=self.collective)

    def get_inquirers(self):
        """ Returns a queryset of all Inquirers that apply to the given criteria """
        interests = self.get_queryset()
        return Inquirer.objects.filter(techcollectiveinterest__in=interests).filter(email_validated=True)


class CollectiveDetailView(AccessRestrictionMixin, FilterDataMixin, TechCollectiveLookupMixin, ListView):
    template_name = "data_analysis/data_analysis_collective_detail.html"

    minimum_results_required = 0

    context_object_name = "initiated_collectives"
    paginate_by = 20

    def get_queryset(self, forms=None):
        return InitiatedCollective.objects.filter(tech_collective=self.collective)
