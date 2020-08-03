from django.forms import Form, ValidationError, fields, widgets
from datetime import datetime

from Questionaire.models import Inquiry, Question
from .models import QuestionFilter


__all__ = ['InquiryCreatedFilterForm', 'InquiryLastVisitedFilterForm', 'InquiryUserExcludeFilterForm',
           'FilterInquiryByQuestionForm']


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

    @classmethod
    def can_filter(cls, **init_kwargs):
        """ A method to determine whether the given filter arguments would yield a form that has use.
         Some forms (like once based on models) might not yield certain output.
         Note: This is irregardless of the given data. Data could yield no filter attributes was called."""
        return True


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

    def has_filter_data(self):
        """ Returns whether this filter has data it filters on """
        if not self.is_valid():
            # If a form is not valid, it should by definition not be filtered
            return False

        for key, value in self.cleaned_data.items():
            # Check if it had any relevant data, if not, there are no values i.e. nothing to filter on.
            if value:
                # A special addition to check that end date is not beyond today i.e. nothing to filter on
                if key == 'end_date':
                    continue
                return True
        return False


class FilterInquiriesMixin:
    """ Returns a queryset of inquiries based on the given filter """
    def get_filtered_inquiries(self, inquiries=None):
        if inquiries is None:
            inquiries = Inquiry.objects.all()
        if self.has_filter_data():
            return self.filter(inquiries)
        else:
            return inquiries


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
    exclude_users = fields.BooleanField(initial=False, required=False, label="Gestart door users")
    exclude_uncompleted = fields.BooleanField(initial=False, required=False)
    prefix = 'filter_users'
    description = "Exclude for..."

    def has_filter_data(self):
        """ Returns whether this filter has data it filters on """
        if not self.is_valid():
            # If a form is not valid, it should by definition not be filtered
            return False

        return any(self.cleaned_data.values())

    def filter(self, data):
        data = super(InquiryUserExcludeFilterForm, self).filter(data)
        if self.cleaned_data["exclude_users"]:
            data = data.filter(inquirer__user=None)
        if self.cleaned_data["exclude_uncompleted"]:
            data = data.filter(is_complete=True)
        return data


class FilterInquiryByQuestionForm(FilterInquiriesMixin, FilterFormBase):
    description = "Filter by question"
    num_questions = fields.IntegerField(initial=0, widget=widgets.HiddenInput)
    prefix = 'filter_q'

    def __init__(self, *args, filter_models=None, **kwargs):
        super(FilterInquiryByQuestionForm, self).__init__(*args, **kwargs)
        self.filter_models = filter_models

        if self.filter_models:
            if len(self.filter_models) == 0:
                # An attribute used in the view to say that it is not used and thus should not be shown
                # This is the case when there are no related filters set
                self.not_used = True
            else:
                i = 0
                for filter_instance in self.filter_models:
                    self.create_fields_for_instance(i, filter_instance)
                    i += 1
                self.fields['num_questions'].initial = len(filter_models)
        elif self.is_bound:
            self.create_fields_from_data()

    def create_fields_for_instance(self, index, filter_instance: QuestionFilter) -> None:
        # Make sure to hide the question widget, it is only to communicate between the originating view and the
        # Chart target view
        question_filter_field = fields.IntegerField(initial=filter_instance.id, widget=widgets.HiddenInput)

        if filter_instance.question.question_type == Question.TYPE_CHOICE:
            # Multiple choice question, get the answers and set the field
            choices = [(-1, '---')]
            for answer in filter_instance.question.answeroption_set.order_by("value"):
                # Make sure to call answer.value, it is the value that it is stored as on the db.
                choices.append((answer.value, answer.answer))

            answer_field = fields.ChoiceField(choices=choices, initial=-1)
        elif filter_instance.question.question_type == Question.TYPE_OPEN:
            answer_field = fields.CharField(required=False)
        else:
            # There is no code implemented for this kind of question, so just return
            return

        answer_field.label = filter_instance.question.name

        self.fields[f'questionfilter_{index}'] = question_filter_field
        self.fields[f'answer_{index}'] = answer_field

    def create_fields_from_data(self):
        # Get the amount of filters that need to be loaded
        try:
            field = self.fields['num_questions']
            value = field.widget.value_from_datadict(
                self.data,
                self.files,
                self.add_prefix('num_questions')
            )
            value = field.clean(value)
        except ValidationError:
            return

        # Loop over all fields
        for i in range(value):
            self.fields[f'questionfilter_{i}'] = fields.IntegerField(initial=-1)
            self.fields[f'answer_{i}'] = fields.CharField()

    def filter(self, data):
        data = super(FilterInquiryByQuestionForm, self).filter(data)
        for i in range(self.cleaned_data['num_questions']):
            # Filter for the specific question
            question_filter = QuestionFilter.objects.get(id=self.cleaned_data[f'questionfilter_{i}'])
            answer = self.cleaned_data[f'answer_{i}']

            if question_filter.question.question_type == Question.TYPE_CHOICE:
                # -1 is the default no answer value
                if answer != "-1":
                    data = data.filter(
                        inquiryquestionanswer__question=question_filter.question,
                        inquiryquestionanswer__answer=answer
                    )
            elif question_filter.question.question_type == Question.TYPE_OPEN:
                if len(answer) > 0:
                    data = data.filter(
                        inquiryquestionanswer__question=question_filter.question,
                        inquiryquestionanswer__answer__icontains=answer
                    )
        return data

    @classmethod
    def can_filter(cls, filter_models=None, **init_kwargs):
        if filter_models is not None:
            return len(filter_models) > 0
        return super(FilterInquiryByQuestionForm, cls).can_filter(**init_kwargs)


