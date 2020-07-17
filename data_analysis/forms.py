from django.forms import Form, DateField, ValidationError
from datetime import datetime


from Questionaire.models import Inquiry


class InquiryFilterForm(Form):
    start_date = DateField(required=False)
    end_date = DateField(required=False, initial=str(datetime.today().date()))

    def clean(self):
        if not (self.cleaned_data['start_date'] or self.cleaned_data['end_date']):
            raise ValidationError('There is nothing to filter with')

        return self.cleaned_data

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

    def get_ranged_inquiries(self):
        start_date = self.cleaned_data['start_date']
        end_date = self.cleaned_data['end_date']

        inquiries = Inquiry.objects.all()
        if start_date:
            inquiries = inquiries.filter(created_on__gte=start_date)
        if end_date:
            inquiries = inquiries.filter(created_on__lte=end_date)

        return inquiries
