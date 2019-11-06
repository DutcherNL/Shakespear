from django.views.generic import TemplateView, View
from django.views.generic.detail import SingleObjectMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

from Questionaire.views import BaseTemplateView

from .models import Information
from .forms import build_moduleform, AddModuleForm, DelModuleForm

# Create your views here.

class PageMixin:
    def get_context_data(self, **kwargs):
        self.information = Information.objects.get(pk=self.kwargs['inf_id'])
        context = super().get_context_data(**kwargs)
        self.information = Information.objects.get(pk=self.kwargs['inf_id'])
        context['page'] = self.information
        context['modules'] = self.information.basemodule_set.order_by('position')
        return context


class InfoPageView(PageMixin, BaseTemplateView):
    template_name = "pagedisplay/page_info_display.html"


class PageAlterView(PageMixin, TemplateView):
    template_name = 'pagedisplay/page_edit_page.html'


class PageAddModuleView(PageMixin, TemplateView):
    template_name = 'pagedisplay/page_edit_add_module.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AddModuleForm(page=self.information)

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        # Add the comment
        form = AddModuleForm(page=self.information, data=request.POST)

        if form.is_valid():
            instance = form.save()

            return HttpResponseRedirect(reverse('edit_page', kwargs={'inf_id': self.information.id,
                                                                     'module_id': instance.id}))
        else:
            context['form'] = form
            return self.render_to_response(context)


class PageAlterModuleView(PageMixin, TemplateView):
    template_name = 'pagedisplay/page_edit_module.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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


class PageDeleteModuleView(View):

    def get(self, request, *args, **kwargs):
        print("GET?")
        return HttpResponseRedirect(reverse('edit_page', kwargs={'inf_id': self.kwargs['inf_id']}))

    def post(self, request, *args, **kwargs):
        print("POST!")
        form = DelModuleForm(self.kwargs['module_id'], data=request.POST)

        if form.is_valid():
            form.execute()
            return HttpResponseRedirect(reverse('edit_page', kwargs={'inf_id': self.kwargs['inf_id']}))

        print(form.errors)
        return HttpResponseRedirect(reverse('edit_page', kwargs={'inf_id': self.kwargs['inf_id'],
                                                                 'module_id': self.kwargs['module_id']}))

