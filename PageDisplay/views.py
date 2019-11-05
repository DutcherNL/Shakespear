from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from Questionaire.views import BaseTemplateView

from .models import Information
from .forms import build_moduleform

# Create your views here.

class InfoPageView(BaseTemplateView):
    template_name = "pagedisplay/page_info_display.html"

    def get_context_data(self, **kwargs):
        context = super(InfoPageView, self).get_context_data(**kwargs)

        information = Information.objects.get(pk=self.kwargs['inf_id'])
        context['page'] = information
        context['modules'] = information.basemodule_set.order_by('position')

        return context


class PageAlterView(TemplateView):
    template_name = 'pagedisplay/page_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        information = Information.objects.get(pk=self.kwargs['inf_id'])
        context['page'] = information
        context['modules'] = information.basemodule_set.order_by('position')

        return context


class PageAlterModuleView(TemplateView):
    template_name = 'pagedisplay/page_edit_module.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.information = Information.objects.get(pk=self.kwargs['inf_id'])
        context['page'] = self.information
        context['modules'] = self.information.basemodule_set.order_by('position')
        self.selected_module = self.information.basemodule_set.get(id=self.kwargs['module_id']).get_child()
        context['selected_module'] = self.selected_module
        context['form'] = build_moduleform(instance=self.selected_module)

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        # Add the comment
        form = build_moduleform(instance=self.selected_module, data=request.POST)

        if form.is_valid():
            form.save()

            return HttpResponseRedirect(reverse('edit_page', kwargs={'inf_id': self.information.id}))
        else:
            context['form'] = form
            return self.render_to_response(context)