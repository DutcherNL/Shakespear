from django.views.generic import TemplateView

from django.shortcuts import render

from .models import Information

# Create your views here.

class InfoPageView(TemplateView):
    template_name = "page_info_display.html"

    def get_context_data(self, **kwargs):
        context = super(InfoPageView, self).get_context_data(**kwargs)

        information = Information.objects.get(pk=self.kwargs['inf_id'])
        context['modules'] = information.basemodule_set.order_by('position')

        return context
