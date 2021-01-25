import datetime

from django.views.generic import ListView, CreateView, TemplateView, View, UpdateView, FormView, DeleteView
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from string import Formatter

from reports.models import *
from reports.responses import PDFResponse
from reports.renderers import ReportSinglePagePDFRenderer, ReportSinglePageRenderer
from reports.forms import *


class AccessabilityMixin(LoginRequiredMixin):
    """ A united mixin that applies for all the reports set-up views
    It is done like this because it makes changing accessiblity (future implementation of permissions) easeier
    """
    pass


class ReportsOverview(AccessabilityMixin, ListView):
    template_name = "reports/setup/reports_overview.html"
    context_object_name = "reports"
    model = Report


class AddReportView(AccessabilityMixin, CreateView):
    model = Report
    fields = ['report_name', 'description', 'file_name']
    template_name = "reports/setup/report_form_add.html"

    def form_valid(self, form):
        result = super(AddReportView, self).form_valid(form)
        ReportDisplayOptions.objects.create(report=self.object)
        return result

    def get_success_url(self):
        url_kwargs = {
            'report_slug': self.object.slug
        }
        return reverse("setup:reports:details", kwargs=url_kwargs)


class ReportMixin:
    report = None

    def dispatch(self, request, *args, **kwargs):
        self.report = get_object_or_404(Report, slug=kwargs.pop('report_slug'))
        return super(ReportMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportMixin, self).get_context_data(**kwargs)
        context['report'] = self.report
        return context


class ReportInfoView(AccessabilityMixin, ReportMixin, TemplateView):
    template_name = "reports/setup/report_detail.html"


class ReportUpdateView(AccessabilityMixin, UpdateView):
    model = Report
    fields = ['report_name', 'description', 'promotion_text', 'file_name', 'is_live']
    slug_url_kwarg = "report_slug"
    template_name_field = "report"
    template_name = "reports/setup/report_form.html"

    def get_success_url(self):
        url_kwargs = {
            'report_slug': self.object.slug
        }
        return reverse("setup:reports:details", kwargs=url_kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportUpdateView, self).get_context_data(**kwargs)
        context['crumb_name'] = "Edit general settings"
        context['crumb_url'] = "setup:reports:edit_report"
        return context


class ReportDisplayOptionsUpdateView(AccessabilityMixin, ReportMixin, UpdateView):
    model = ReportDisplayOptions
    fields = "__all__"
    template_name = "reports/setup/report_form.html"

    def get_object(self, queryset=None):
        # If the report has no display options, create the display options
        return ReportDisplayOptions.objects.get_or_create(report=self.report)[0]

    def get_context_data(self, **kwargs):
        context = super(ReportDisplayOptionsUpdateView, self).get_context_data(**kwargs)
        context['crumb_name'] = "Edit display options"
        context['crumb_url'] = "setup:reports:edit_display"
        return context

    def get_success_url(self):
        url_kwargs = {
            'report_slug': self.report.slug
        }
        return reverse("setup:reports:details", kwargs=url_kwargs)


# #######################################################################
# ################        Page Layout Views       #######################
# #######################################################################


class ReportLayoutListView(AccessabilityMixin, ReportMixin, ListView):
    template_name = "reports/setup/layouts/layout_overview.html"
    context_object_name = "layouts"

    def get_queryset(self):
        return PageLayout.objects.filter(report=self.report)

    def get_context_data(self):
        paper_size = self.report.display_options.get_paper_sizes_mm()

        kwargs = super(ReportLayoutListView, self).get_context_data()
        kwargs.update({
            # preview width is set in em
            'preview_width': 10,
            'preview_height': 10 * paper_size['height'] / paper_size['width'],
            'preview_scale': 0.4,
        })
        return kwargs


class ReportAddLayoutView(AccessabilityMixin, ReportMixin, CreateView):
    model = PageLayout
    fields = ['name', 'description', 'template', 'margins']
    template_name = "reports/setup/layouts/create_layout.html"

    def get_form(self, form_class=None):
        form = super(ReportAddLayoutView, self).get_form(form_class=form_class)
        # Set the report on the form instance
        form.instance.report = self.report
        return form

    def get_success_url(self):
        return reverse('setup:reports:edit_layout', kwargs={'report_slug': self.report.slug, 'layout': self.object})


class LayoutMixin:
    layout = None

    def dispatch(self, request, *args, layout=None, **kwargs):
        self.layout = layout
        if self.layout.report != self.report:
            raise Http404("The selected layout is not part of this report")
        return super(LayoutMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(LayoutMixin, self).get_context_data(**kwargs)
        context['layout'] = self.layout
        return context


class PreviewLayoutMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report_display_options = self.report.display_options
        context.update({
            'layout_context': {
                'header': self.layout.report.display_options.header,
                'footer': self.layout.report.display_options.footer,
            },
            'measurements': {
                'margins': self.layout.margins,
                'size': report_display_options.paper_proportions
            }

        })
        return context


class ReportChangeLayoutSettingsView(AccessabilityMixin, ReportMixin, LayoutMixin, PreviewLayoutMixin, UpdateView):
    fields = ['name', 'description']
    template_name = "reports/setup/layouts/edit_layout_settings.html"

    def get_object(self, queryset=None):
        return self.layout

    def get_success_url(self):
        return reverse('setup:reports:edit_layout', kwargs={'report_slug': self.report.slug, 'layout': self.layout})


class ReportChangeLayoutView(AccessabilityMixin, ReportMixin, LayoutMixin, PreviewLayoutMixin, FormView):
    template_name = "reports/setup/layouts/edit_layout.html"
    form_class = AlterLayoutForm

    def get_form_kwargs(self):
        kwargs = super(ReportChangeLayoutView, self).get_form_kwargs()
        kwargs.update({
            'instance': self.layout,
        })
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(ReportChangeLayoutView, self).form_valid(form)

    def get_success_url(self):
        return reverse('setup:reports:edit_layout', kwargs={'report_slug': self.report.slug, 'layout': self.layout})


# #######################################################################
# #################        Page Setup Views      ########################
# #######################################################################


class CreateReportPageView(AccessabilityMixin, ReportMixin, CreateView):
    model = ReportPage
    fields = ['name', 'description', 'layout']
    template_name = "reports/setup/reportpage_form_add.html"

    def get_success_url(self):
        url_kwargs = {
            'report_slug': self.report.slug,
            'report_page_id': self.object.id
        }
        return reverse("setup:reports:details", kwargs=url_kwargs)

    def form_valid(self, form):
        form.instance.report = self.report
        result = super(CreateReportPageView, self).form_valid(form)

        try:
            page_num = ReportPageLink.objects.filter(report=self.report).order_by('page_number').last().page_number + 1
        except AttributeError:
            # There is no page yet
            page_num = 1

        ReportPageLink.objects.create(
            report=self.report,
            page=form.instance,
            page_number=page_num
        )
        return result


class ReportMovePageView(AccessabilityMixin, ReportMixin, FormView):
    form_class = MovePageForm

    def get(self, request, *args, **kwargs):
        messages.error(request, message="The page you tried to visit is unvisitable and only used to process data. "
                                        "You have been redirected to this page instead")
        return HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super(ReportMovePageView, self).get_form_kwargs()
        kwargs.update({
            'report': self.report
        })
        return kwargs

    def form_valid(self, form):
        form.save()
        direction = "upward" if form.cleaned_data['move_up'] else "downward"
        page = form.cleaned_data['report_page']

        messages.success(self.request, f"Succesfully moved {page} {direction}")
        return super(ReportMovePageView, self).form_valid(form)

    def form_invalid(self, form):
        invalidation_errors = form.errors.as_data()
        first_form_error = invalidation_errors.get(list(invalidation_errors.keys())[0])[0]

        messages.error(self.request, f"An error occured: {first_form_error}")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('setup:reports:details', kwargs={'report_slug': self.report.slug})


class CreateReportMultiPageView(CreateReportPageView):
    fields = ['name', 'description', 'layout', 'multi_type']

    def get_form(self, form_class=None):
        form = super(CreateReportMultiPageView, self).get_form(form_class=form_class)
        form.fields['multi_type'].required = True
        return form


class ReportPageMixinPrep:
    report_page = None

    def dispatch(self, request, *args, **kwargs):
        self.report_page = get_object_or_404(ReportPage, id=kwargs.pop('report_page_id'), reportpagelink__report=self.report)
        return super(ReportPageMixinPrep, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReportPageMixinPrep, self).get_context_data(**kwargs)
        context['report_page'] = self.report_page
        return context


class ReportPageMixin(AccessabilityMixin, ReportMixin, ReportPageMixinPrep):
    # It is done this way to ensure that the link report_page and report is confirmed before anything else is done
    pass


# Todo: redact these views, they are part of the sitedisplay options now
class ReportPageInfoView(ReportPageMixin, TemplateView):
    template_name = "reports/setup/reportpage_detail.html"


class ReportPageUpdateView(AccessabilityMixin, ReportMixin, UpdateView):
    model = ReportPage
    fields = ['name', 'description', 'layout']
    pk_url_kwarg = "report_page_id"
    template_name_field = "report_page"

    def get_success_url(self):
        url_kwargs = {
            'report_slug': self.report.slug,
            'report_page_id': self.object.id
        }
        return reverse("setup:reports:details", kwargs=url_kwargs)


# #######################################################################
# ################# Report Page Display Criteria ########################
# #######################################################################


class ReportPageCriteriaOverview(ReportPageMixin, ListView):
    paginate_by = 100
    template_name = "reports/setup/page_conditions/reportpage_criteria_list.html"

    def get_queryset(self):
        return self.report_page.pagecriteria_set.order_by('page_id')


class CreateTechCriteriaView(ReportPageMixin, CreateView):
    template_name = "reports/setup/page_conditions/reportpage_criteria_create.html"
    model = TechnologyPageCriteria
    fields = ['technology', 'score']

    def form_valid(self, form):
        form.instance.page = self.report_page
        form.save()
        return super(CreateTechCriteriaView, self).form_valid(form)

    def get_success_url(self):
        return reverse("setup:reports:page_criterias",
                       kwargs={'report_page_id': self.report_page.id, 'report_slug': self.report.slug})


class EditCriteriaView(ReportPageMixin, UpdateView):
    template_name = "reports/setup/page_conditions/reportpage_criteria_edit.html"
    model = TechnologyPageCriteria
    fields = ['technology', 'score']

    def get_object(self, queryset=None):
        object = self.report_page.pagecriteria_set.filter(id=self.kwargs.get('criteria_id', None))
        try:
            object = object.get()
        except PageCriteria.DoesNotExist:
            raise Http404("This criteria is not associated to this page")
        return object.get_as_child()

    def get_success_url(self):
        return reverse("setup:reports:page_criterias",
                       kwargs={'report_page_id': self.report_page.id, 'report_slug': self.report.slug})


class DeleteCriteriaView(ReportPageMixin, DeleteView):
    template_name = "reports/setup/page_conditions/reportpage_criteria_delete.html"
    model = PageCriteria

    def get_object(self, queryset=None):
        object = self.report_page.pagecriteria_set.filter(id=self.kwargs.get('criteria_id', None))
        try:
            object = object.get()
        except PageCriteria.DoesNotExist:
            raise Http404("This criteria is not associated to this page")
        return object

    def get_success_url(self):
        return reverse("setup:reports:page_criterias",
                       kwargs={'report_page_id': self.report_page.id, 'report_slug': self.report.slug})


# #######################################################################
# #################       Print output views     ########################
# #######################################################################


class PDFTemplateView(TemplateResponseMixin, ContextMixin, View):
    """A view that adjusts the templatemixin to display the template in PDF form.
    It overrides all code from TemplateView class, thus does not inherit from it directly """
    template_engine = "PDFTemplates"
    response_class = PDFResponse
    file_name = 'test_file'
    page_renderer_class = ReportSinglePagePDFRenderer

    def get_file_name(self):
        """ Construct the file name from the given file name replaced with local attributes """

        # Execute a manual f- replacing input elements with local variables
        rep_string = self.file_name  # Set the sanalysed string

        # Deconstruct the string to get the keys
        formatter = Formatter()
        keys = []
        for literal, key, format, conversion in formatter.parse(self.file_name):
            keys.append(key)

        for key in keys:
            # Split the chains (e.g. object.attribute1.attribute2)
            attr_chain = key.split('.')
            replacement = self  # The current selected object in the chain, start with the view
            processed_key = 'view'  # Construct an identifying string for error reporting/ format clearing
            for attr in attr_chain:
                # Get the attribute
                if hasattr(replacement, attr):
                    replacement = replacement.__getattribute__(attr)
                elif isinstance(replacement, dict) and attr in replacement:
                    replacement = replacement.get(attr)
                else:
                    raise AttributeError(f'Incorrect file name"{attr}" was not an attribute of {processed_key}')
                processed_key += '.' + attr  # Update the processed_key (successfully retrieved these parameters)

                if callable(replacement):
                    # Check if it is a function, if it is, use that function
                    replacement = replacement()

            # Replace the entry with the proper object
            rep_string = rep_string.replace("{"+key+"}", str(replacement))
        return rep_string

    def get_context_data(self, **kwargs):
        context = super(PDFTemplateView, self).get_context_data(**kwargs)
        context['renderer'] = self.page_renderer_class
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        # Send along the file name of the file
        return self.render_to_response(context, file_name=self.get_file_name(), page_options=self.get_page_options())

    def get_page_options(self):
        return {}


class PrintPageAsPDFView(ReportPageMixin, PDFTemplateView):
    template_name = "reports/pdf_page.html"
    file_name = 'Example_pdf_page_{report_page.id}'

    def get_context_data(self):
        context = super(PrintPageAsPDFView, self).get_context_data()
        context['template_engine'] = self.template_engine
        return context

    def get_page_options(self):
        options = super(PrintPageAsPDFView, self).get_page_options()
        orientation = 'Portrait' if self.report_page.reportpagelink.report.display_options.orientation else 'Landscape'

        options.update({
            'page-size': self.report_page.reportpagelink.report.display_options.size,
            'orientation': orientation,
        })
        return options


class PrintPageAsHTMLView(ReportPageMixin, TemplateView):
    template_name = "reports/pdf_page.html"
    template_engine = "PDFTemplates"


class PrintReportAsPDFView(ReportMixin, PDFTemplateView):
    template_name = "reports/pdf_report.html"
    file_name = 'Example_report_{report.id}'

    def get_context_data(self):
        context = super(PrintReportAsPDFView, self).get_context_data()
        context['template_engine'] = self.template_engine
        context['pages'] = self.report.get_pages()
        return context


class PrintReportAsHTMLView(AccessabilityMixin, ReportMixin, TemplateView):
    template_name = "reports/pdf_report.html"
    template_engine = "PDFTemplates"

    def get_context_data(self):
        context = super(PrintReportAsHTMLView, self).get_context_data()
        context['pages'] = self.report.get_pages()
        return context