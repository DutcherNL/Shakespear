from django.views.generic import TemplateView, View
from django.http import JsonResponse

from Questionaire.models import Inquiry, Page

from .forms import InquiryFilterForm


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
            options.update({
                'title': {
                    'display': True,
                    'text': self.title
                }
            })

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


class InquiryProgressChart(JsonChartView):
    chart_type = 'bar'
    title = "Inquiry progress"
    chart_options = {
        'responsive': True,
        'scales': {
            'yAxes': [{
                'ticks': {
                    'beginAtZero': True
                }
            }]
        }
    }

    def compute_chart_labels(self):
        labels = ['Total']
        for page in Page.objects.order_by('position'):
            labels.append(f'Page {page.position}')
        return labels

    def compute_chart_data(self):
        data = super(InquiryProgressChart, self).compute_chart_data()

        print(self.request.GET)
        if len(self.request.GET)>0:
            # If a filter is applied, create a similar run with the filter applied
            form = InquiryFilterForm(self.request.GET)
            if form.is_valid():
                data.append(ChartData(
                    self.compute_single_chart_run(inquiries=form.get_ranged_inquiries()),
                    label="Filtered inquiries",
                    borderColor='#808080',
                    backgroundColor='#808080',
                ))

        # Convert it to percentages
        data.append(
            ChartData(
                self.compute_single_chart_run(),
                label="Communilative progress",
                borderColor='#A2A2A2',
                backgroundColor='#A2A2A2',
            )
        )
        return data

    def compute_single_chart_run(self, inquiries=None):
        """
        Computes a single datarun for the given inquiryset
        :param inquiries:
        :return:
        """
        inquiries = inquiries or Inquiry.objects.all()

        remaining_inquiries = inquiries.count()
        data = [remaining_inquiries]

        for page in Page.objects.order_by('position'):
            remaining_inquiries -= inquiries.filter(current_page=page).count()
            data.append(remaining_inquiries)

        data.append(inquiries.filter(current_page=None).count())
        return [round(x * 100 / float(data[0]), 2) for x in data]

