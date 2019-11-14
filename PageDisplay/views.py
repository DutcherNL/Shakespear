from django.views.generic import TemplateView, View
from django.views.generic.list import ListView
from django.http import HttpResponseRedirect
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

    def __init__(self, *args, **kwargs):
        super(PageAddModuleView, self).__init__(*args, **kwargs)
        self.position = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if len(self.request.GET) == 0:
            root_form = AddModuleForm(information=self.information)
        else:
            root_form = AddModuleForm(information=self.information, data=self.request.GET)

            if root_form.is_valid():
                instance = root_form.get_instance()
                self.position = instance.position
                root_form.make_hidden()

                context['module_form'] = build_moduleform(instance=instance)

        context['root_form'] = root_form

        # Get the item it is placed in front of:
        if self.position:
            for module in self.information.basemodule_set.order_by('position'):
                if module.position > self.position:
                    context['module_after_new'] = module
                    break

        return context

    def set_forms(self, root_data=None, module_data=None):
        root_form = AddModuleForm(information=self.information, data=root_data)

        if root_form.is_valid():
            # class_type = form.get_obj_class()
            instance = root_form.get_instance()

            module_form = build_moduleform(instance=instance, data=module_data)
            return root_form, module_form
        return root_form, None

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        root_form = AddModuleForm(information=self.information, data=self.request.POST)

        if root_form.is_valid():
            instance = root_form.get_instance()

            module_form = build_moduleform(instance=instance, data=request.POST)
            if module_form.is_valid():
                module_form.save()
                return HttpResponseRedirect(reverse('edit_page', kwargs={'inf_id': self.information.id}))

            context['module_form'] = module_form

        return self.render_to_response(context)


class PageAddModuleDetailsView(PageMixin, TemplateView):
    template_name = 'pagedisplay/page_edit_add_module_details.html'


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
        form = build_moduleform(instance=self.selected_module, data=request.POST, files=request.FILES)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('edit_page', kwargs={'inf_id': self.information.id}))
        else:
            context['form'] = form
            return self.render_to_response(context)


class PageDeleteModuleView(View):

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('edit_page', kwargs={'inf_id': self.kwargs['inf_id']}))

    def post(self, request, *args, **kwargs):
        form = DelModuleForm(self.kwargs['module_id'], data=request.POST)

        if form.is_valid():
            form.execute()
            return HttpResponseRedirect(reverse('edit_page', kwargs={'inf_id': self.kwargs['inf_id']}))

        return HttpResponseRedirect(reverse('edit_page', kwargs={'inf_id': self.kwargs['inf_id'],
                                                                 'module_id': self.kwargs['module_id']}))


class PageOverview(ListView):
    model = Information
    context_object_name = "pages"
    template_name = "pagedisplay/pages_overview.html"
