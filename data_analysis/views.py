import urllib
from datetime import timedelta

from django.utils import timezone
from django.db.models import Count, Q
from django.views.generic import TemplateView, ListView
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


class AccessRestrictionMixin(PermissionRequiredMixin):
    """ A view that restricts access to only those who are authorized """
    permission_required = 'auth.can_access_data_analysis_pages'


class FilterDataMixin:
    form_classes = []
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

    def get_form_kwargs(self, form_class):
        return {}

    def get_queryset(self, forms=None):
        """ Returns the queryset of the main object analysed """
        # If no forms are given initialise local forms
        if forms is None:
            get_data = self.request.GET if self.request.GET else None
            forms = []
            for form_class in self.form_classes:
                if form_class.can_filter(data=get_data, **self.get_form_kwargs(form_class)):
                    form = form_class(get_data, **self.get_form_kwargs(form_class))
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
        for form_class in self.form_classes:
            if form_class.can_filter(data=get_data, **self.get_form_kwargs(form_class)):
                form = form_class(get_data, **self.get_form_kwargs(form_class))
                forms[str(form.name) + ""] = form

        return forms


class InquiryDataView(AccessRestrictionMixin, FilterDataMixin, TemplateView):
    template_name = "data_analysis/data_analysis_inquiry_progress.html"
    form_classes = [InquiryLastVisitedFilterForm, InquiryUserExcludeFilterForm, FilterInquiryByQuestionForm]

    def get_form_kwargs(self, form_class):
        kwargs = super(InquiryDataView, self).get_form_kwargs(form_class)
        if form_class is FilterInquiryByQuestionForm:
            kwargs.update({
                'filter_models': QuestionFilter.objects.filter(use_for_progress_analysis=True)
            })
        return kwargs


class TechDataView(AccessRestrictionMixin, FilterDataMixin, TemplateView):
    template_name = "data_analysis/data_analysis_techs.html"
    form_classes = [InquiryLastVisitedFilterForm,
                    FilterInquiryByQuestionForm, InquiryUserExcludeFilterForm]

    def get_context_data(self, **kwargs):
        return super(TechDataView, self).get_context_data(
            techs=Technology.objects.all(),
            **kwargs
        )

    def get_form_kwargs(self, form_class):
        kwargs = super(TechDataView, self).get_form_kwargs(form_class)
        if form_class is FilterInquiryByQuestionForm:
            kwargs.update({
                'filter_models': QuestionFilter.objects.filter(use_for_tech_analysis=True)
            })
        return kwargs


class InterestsView(AccessRestrictionMixin, FilterDataMixin, TemplateView):
    template_name = "data_analysis/data_analysis_interests.html"
    form_classes = [FilterInterestByInquirerCreationDateForm]

    def get_context_data(self, **kwargs):
        context = super(InterestsView, self).get_context_data(**kwargs)
        queryset = context['queryset']
        context['interests'] = self.get_interest_data(queryset=queryset)
        return context

    def get_interest_data(self, queryset=None):
        if queryset is None:
            queryset = TechCollectiveInterest.objects.all()

        interests = queryset.filter(is_interested=True)

        data = []
        for collective in TechCollective.objects.filter():

            ids = []
            for interest in interests:
                ids.append(interest.inquirer.id)

            data.append({
                'technology': collective.technology,
                'count': interests.filter(tech_collective=collective).count(),
            })
        return data


class TechCollectiveLookupMixin:
    collective = None

    def dispatch(self, request, *args, **kwargs):
        self.collective = get_object_or_404(TechCollective, technology__slug=self.kwargs['tech_slug'])
        return super(TechCollectiveLookupMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TechCollectiveLookupMixin, self).get_context_data(**kwargs)

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
        context['technology'] = self.collective.technology

        return context


class InterestDetailView(AccessRestrictionMixin, TechCollectiveLookupMixin, FilterDataMixin, TemplateView):
    template_name = "data_analysis/data_analysis_interest_detail.html"
    form_classes = [FilterInterestByInquirerCreationDateForm, FilterInterestByRestrictionForm]
    minimum_results_required = 0

    def get_context_data(self, **kwargs):
        context = super(InterestDetailView, self).get_context_data(**kwargs)

        # Restrict the results to this collective only
        context['queryset'] = context['queryset'].filter(tech_collective=self.collective)
        context['queryset_interested'] = context['queryset'].filter(is_interested=True)

        return context

    def get_form_kwargs(self, form_class):
        kwargs = super(InterestDetailView, self).get_form_kwargs(form_class)
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
    template_name = "data_analysis/data_analysis_interest_restriction_list.html"
    form_classes = [FilterInterestByInquirerCreationDateForm, FilterInterestByRestrictionForm]

    recent_days_count = 7
    minimum_results_required = 0

    # Listable attribute
    context_object_name = "restriction_list"
    paginate_by = 20
    ordering = 'value'

    def dispatch(self, request, *args, **kwargs):
        return super(InterestRestrictionListView, self).dispatch(request, *args, **kwargs)

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
        return super(InterestRestrictionListView, self).get_context_data(
            recent_dayscount=self.recent_days_count,
            **kwargs)

    def get_form_kwargs(self, form_class):
        kwargs = super(InterestRestrictionListView, self).get_form_kwargs(form_class)
        if form_class is FilterInterestByRestrictionForm:
            kwargs.update({
                'collective': self.collective,
            })
        return kwargs
