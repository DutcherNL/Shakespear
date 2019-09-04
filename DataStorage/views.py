from django.views.generic import TemplateView, FormView

from .forms import DataLookupForm, DataUploadForm

# Create your views here.


class DataLookupView(TemplateView):
    template_name = "data_retrival.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = DataLookupForm(self.request.GET)
        return context


class DataUploadFromCSVView(FormView):
    template_name = 'contact.html'
    form_class = DataUploadForm
