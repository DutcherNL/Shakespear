from django.views.generic import TemplateView

from .forms import DataLookupForm

# Create your views here.


class DataLookupView(TemplateView):
    template_name = "data_retrival.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = DataLookupForm(self.request.GET)
        return context