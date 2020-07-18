from django.forms import Form, ValidationError, fields
from datetime import datetime

from Questionaire.models import Inquiry


__all__ = ['InquiryCreatedFilterForm', 'InquiryLastVisitedFilterForm', 'InquiryUserExcludeFilterForm']


class FilterFormBase(Form):
    """ A base form that can be used as mixin to for forms that should filter data based on a specific attribute """
    description = None

    def has_filter_data(self):
        """ Returns whether this filter has data it filters on """
        if not self.is_valid():
            # If a form is not valid, it should by definition not be filtered
            return False

        for value in self.cleaned_data.values():
            # Check if it had any relevant data, if not, there are no values i.e. nothing to filter on.
            if value:
                return True
        return False

    def filter(self, data):
        return data


class DateRangeFilterForm(FilterFormBase):
    start_date = fields.DateField(required=False)
    end_date = fields.DateField(required=False, initial=str(datetime.today().date()))
    filter_attribute_name = None

    def __new__(cls, *args, **kwargs):
        class_obj = super(DateRangeFilterForm, cls).__new__(cls)
        assert class_obj.filter_attribute_name is not None
        return class_obj

    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        if start_date:
            if start_date > datetime.today().date():
                raise ValidationError('Start date can not be later than today', code='out-of-range')

        return start_date

    def clean_end_date(self):
        start_date = self.cleaned_data['start_date']
        end_date = self.cleaned_data['end_date']
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError('End date can not preceed start date', code='incorrect-order')

        return end_date

    def filter(self, data):
        """ Filters the filtered attribute on the given range """
        start_date = self.cleaned_data['start_date']
        end_date = self.cleaned_data['end_date']

        data = super(DateRangeFilterForm, self).filter(data)

        if start_date:
            filter_name = f'{self.filter_attribute_name}__gte'
            data = data.filter(**{
                filter_name: start_date
            })
        if end_date:
            filter_name = f'{self.filter_attribute_name}__lte'
            data = data.filter(**{
                filter_name: end_date
            })

        return data


class FilterInquiriesMixin:
    """ Returns a queryset of inquiries based on the given filter """
    def get_filtered_inquiries(self, inquiries=None):
        if inquiries is None:
            inquiries = Inquiry.objects.all()

        return self.filter(inquiries)


class InquiryCreatedFilterForm(FilterInquiriesMixin, DateRangeFilterForm):
    filter_attribute_name = "created_on"
    prefix = "created_on"
    description = "Filter creation date"


class InquiryLastVisitedFilterForm(FilterInquiriesMixin, DateRangeFilterForm):
    filter_attribute_name = "last_visited"
    prefix = "last_visited"
    description = "Filter last visitation date"


class InquiryUserExcludeFilterForm(FilterInquiriesMixin, FilterFormBase):
    """ A checkbox that marks whether Inquiries made by Users should be ignored """
    filter_users = fields.BooleanField(initial=False, required=False)
    prefix = 'filter_users'
    description = "Exclude created by site users"

    def has_filter_data(self):
        """ Returns whether this filter has data it filters on """
        if not self.is_valid():
            # If a form is not valid, it should by definition not be filtered
            return False

        return self.cleaned_data['filter_users']

    def filter(self, data):
        data = super(InquiryUserExcludeFilterForm, self).filter(data)
        if self.cleaned_data['filter_users']:
            data = data.filter(inquirer__user=None)
        return data




