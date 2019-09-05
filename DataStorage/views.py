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
    template_name = 'data_upload_form.html'
    form_class = DataUploadForm
    success_url = "/data/add/"

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.process()
        return super(DataUploadFromCSVView, self).form_valid(form)
