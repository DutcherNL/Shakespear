import datetime
from django.views.generic import View
from django.http import JsonResponse

from Questionaire.models import Inquiry, Page

from .forms import *


class ChartData(dict):
    """
    A datadict structure to store chart data in. Data adheres ChartJS structure.
    Check out www.chartjs.org/docs for information on the data attributes you can use.
    """
    label = None
    data = []

    def __init__(self, *args, **kwargs):
        """
        Initialises the chart data
        :param args:
        """
        super(ChartData, self).__init__()

        if len(args) == 1 and isinstance(args[0], list):
            self.data = args[0]
        else:
            self.data = args

        for key, value in kwargs.items():
            self[key] = value

    def get_as_dict(self):
        dict_form = {
            'data': self.data,
            **self
        }

        return dict_form


class ChartAxis(dict):
    """
    A data object representing axis data as represented in the tick options of ChartJs.
    For more info on customisation check the ChartJs Docs:
    https://www.chartjs.org/docs/latest/axes/
    """
    # Entries in rename set rename certain keys to the secondary key when processing to Json dict
    rename_sets = [('label', 'labelString'), ('display_label', 'display')]
    # Attr sets to ensure these attributes end at the correct location
    tick_attrs = ['beginAtZero', 'suggestedMin', 'suggestedMax', 'maxTicksLimit', 'stepSize', 'precision']
    label_attrs = ['display', 'labelString', 'lineHeight', 'fontSize', 'fontStyle', 'padding']

    def __init__(self, **kwargs):
        """
        Initialises the chart data
        :param args:
        """
        super(ChartAxis, self).__init__()

        for key, value in kwargs.items():
            self[key] = value

    def _rename_key(self, key):
        """ Returns a corrected name for the given key, allows more sensibl naming of certain normal attributes """
        for rename_couple in self.rename_sets:
            if rename_couple[0] == key:
                return rename_couple[1]
        return key

    def get_as_dict(self):
        """ Returns a JSON ready dict format"""
        if self['label']:
            self['display'] = True

        ticks = {}
        label = {}
        outer = {}
        # Set all data that can be set in ticks in ticks
        for key, value in self.items():
            key = self._rename_key(key)
            if key in self.tick_attrs:
                ticks[key] = value
            elif key in self.label_attrs:
                label[key] = value
            else:
                outer[key] = value

        dict_form = {
            'ticks': ticks,
            'scaleLabel': label,
            **outer
        }
        return dict_form


class JsonChartView(View):
    """ A view that constructs data for a chart and returns it in JSON format.
        To define your data use compute_chart_data to compute the datasets stored as ChartData objects.
        Read the ChartData docs to know what options are possible.

     """
    datasets = []
    chart_type = None
    chart_options = {
        'responsive': True,
    }
    title = None
    legend = None

    def get(self, request, *args, **kwargs):
        # Reset the datasets
        self.labels = self.compute_chart_labels()
        self.datasets = self.compute_chart_data()
        return JsonResponse(data=self.get_data())

    def compute_chart_labels(self):
        """ Compute the chart labels"""
        return []

    def compute_chart_data(self, *data):
        """ Compute the chart data and store them in ChartData instances. Returns a list of ChartData dicts"""
        return [*data]

    def get_data(self):
        return {
            'chart_type': self.chart_type,
            'data': self.get_chart_data(),
            'options': self.get_chart_options(),
        }

    def get_chart_options(self):
        # Create a local copy
        options = self.chart_options.copy()
        if self.title:
            options.update(**{
                'title': {
                    'display': True,
                    'text': self.title
                }
            })

        # Set the axes
        if hasattr(self, 'yAxis') or hasattr(self, 'xAxis'):
            # Note that by design we assume a single axis, however ChartJs expects Axes so place tham in a list
            # Also note that the expected name is Axes not axis!
            scales = {}
            if hasattr(self, 'xAxis'):
                if isinstance(self.xAxis, ChartAxis):
                    scales['xAxes'] = [self.xAxis.get_as_dict()]
            if hasattr(self, 'yAxis'):
                if isinstance(self.yAxis, ChartAxis):
                    scales['yAxes'] = [self.yAxis.get_as_dict()]
            options['scales'] = scales

        if self.legend:
            options['legend'] = self.legend

        return options

    def get_chart_data(self, **kwargs):
        chart_data = {}
        if hasattr(self, 'labels'):
            chart_data['labels'] = self.labels

        datasets = []
        for data_set in self.datasets:
            if isinstance(data_set, ChartData):
                datasets.append(data_set.get_as_dict())
            elif isinstance(data_set, dict):
                datasets.append(data_set)
            else:
                raise ValueError("Stored dataset is not ChartData object or a dict with similar attributes")
        chart_data['datasets'] = datasets

        chart_data.update(kwargs)
        return chart_data


class DataFilterMixin:
    """ Applies form filters to the inquiry queryset """
    form_classes = []
    model_class = None

    def __init__(self, *args, **kwargs):
        super(DataFilterMixin, self).__init__(*args, **kwargs)
        self.has_filtered = False

    def filter_data(self, data=None):
        if data is None:
            data = self.model_class.objects.all()
        self.has_filtered = False

        for form_class in self.form_classes:
            form = form_class(self.request.GET)
            if form.has_filter_data():
                data = form.filter(data)
                self.has_filtered = True

        return data


class InquiryProgressChart(DataFilterMixin, JsonChartView):
    form_classes = [InquiryCreatedFilterForm, InquiryLastVisitedFilterForm]
    model_class = Inquiry
    chart_type = 'bar'
    title = "Inquiry progress"
    yAxis = ChartAxis(beginAtZero=True, label="% passed page")
    legend = {'position': 'right'}

    def compute_chart_labels(self):
        labels = ['Total']
        for page in Page.objects.order_by('position'):
            labels.append(f'Page {page.position}')
        return labels

    def compute_chart_data(self):
        data = super(InquiryProgressChart, self).compute_chart_data()

        inquiries = self.filter_data()
        if self.has_filtered:
            data.append(ChartData(
                self.compute_single_chart_run(inquiries=inquiries),
                label="Filtered",
                borderColor='#808080',
                backgroundColor='#808080',
            ))

        # Convert it to percentages
        data.append(
            ChartData(
                self.compute_single_chart_run(),
                label="All",
                borderColor='#A2A2A2',
                backgroundColor='#A2A2A2',
            )
        )
        return data

    @staticmethod
    def compute_single_chart_run(inquiries=None):
        """
        Computes a single datarun for the given inquiryset
        :param inquiries:
        :return:
        """
        if inquiries is None:
            # It could be that inquiries is an empty dataset, that is fine.
            inquiries = Inquiry.objects.all()

        remaining_inquiries = inquiries.count()
        data = [remaining_inquiries]
        if remaining_inquiries == 0:
            # Catch on an empty queryset. (to prevent devision by zero
            return [0 for page in Page.objects.all()]

        for page in Page.objects.order_by('position'):
            remaining_inquiries -= inquiries.filter(current_page=page).count()
            data.append(remaining_inquiries)

        data.append(inquiries.filter(current_page=None).count())
        return [round(x * 100 / float(data[0]), 2) for x in data]


class InquiryCreationChart(DataFilterMixin, JsonChartView):
    form_classes = [InquiryCreatedFilterForm, InquiryLastVisitedFilterForm]
    model_class = Inquiry
    chart_type = 'line'
    title = "Daily inquiry creation"
    legend = {'display': None}

    def __init__(self, *args, **kwargs):
        super(InquiryCreationChart, self).__init__(*args, **kwargs)
        yAxis = ChartAxis(beginAtZero=True, label="Daily new inquirers")
        xAxis = ChartAxis(label="Date")

    def compute_chart_labels(self):
        inquiries = self.filter_data()
        inquiries = inquiries.order_by('created_on')

        self.start_date = inquiries.first().created_on.date()
        self.end_date = inquiries.last().created_on.date()
        self.days_dif = (self.end_date - self.start_date).days

        # Set the maximum number of ticks to one tick a week unless its less than two weeks
        if self.days_dif <= 14:
            self.xAxis['maxTicksLimit'] = self.days_dif / 7 + 1

        labels = [self.start_date + datetime.timedelta(days=i) for i in range(self.days_dif)]
        return labels

    def compute_chart_data(self):
        data = super(InquiryCreationChart, self).compute_chart_data()

        from django.db.models.functions import TruncDay
        from django.db.models import Count

        inquiries = self.filter_data()
        inquiries = inquiries.annotate(creation_day=TruncDay('created_on')).values('creation_day')
        inquiries = inquiries.annotate(num_created=Count('id')).values('creation_day', 'num_created')

        inquiry_iteration = iter(inquiries)

        line_data = []
        next_date = next(inquiry_iteration)
        next_date_at = (next_date.get('creation_day').date() - self.start_date).days

        for i in list(range(0, self.days_dif)):
            if i == next_date_at:
                line_data.append(next_date.get('num_created'))
                try:
                    next_date = next(inquiry_iteration)
                    next_date_at = (next_date.get('creation_day').date() - self.start_date).days
                except StopIteration:
                    next_date = None
                    next_date_at = -1
            else:
                line_data.append(0)

        data.append(ChartData(
            line_data,
        ))


        return data
