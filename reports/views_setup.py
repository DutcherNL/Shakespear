from django.views.generic import ListView, CreateView, TemplateView, View, UpdateView
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from string import Formatter
from .models import Report, ReportPage, ReportDisplayOptions
from .responses import PDFResponse


class ReportsOverview(ListView):
    template_name = "reports/reports_overview.html"
    context_object_name = "reports"
    model = Report


class AddReportView(CreateView):
    model = Report
    fields = ['report_name', 'description', 'file_name']
    template_name = "reports/report_form_add.html"

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

    def get_context_data(self):
        context = super(ReportMixin, self).get_context_data()
        context['report'] = self.report
        return context


class ReportInfoView(ReportMixin, TemplateView):
    template_name = "reports/report_detail.html"


class ReportUpdateView(UpdateView):
    model = Report
    fields = ['description', 'file_name']
    slug_url_kwarg = "report_slug"
    template_name_field = "report"

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


class ReportDisplayOptionsUpdateView(ReportMixin, UpdateView):
    model = ReportDisplayOptions
    fields = "__all__"
    template_name = "reports/report_form.html"

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


class CreateReportPageView(ReportMixin, CreateView):
    model = ReportPage
    fields = ['name', 'description', 'page_number']
    template_name = "reports/reportpage_form_add.html"

    def form_valid(self, form):
        form.instance.report = self.report
        return super(CreateReportPageView, self).form_valid(form)

    def get_initial(self):
        initials = super(CreateReportPageView, self).get_initial()
        initials['report'] = self.report
        return initials

    def get_success_url(self):
        url_kwargs = {
            'report_slug': self.report.slug,
            'report_page_id': self.object.id
        }
        return reverse("setup:reports:details", kwargs=url_kwargs)


class ReportPageMixinPrep:
    report_page = None

    def dispatch(self, request, *args, **kwargs):
        self.report_page = get_object_or_404(ReportPage, id=kwargs.pop('report_page_id'), report=self.report)
        return super(ReportPageMixinPrep, self).dispatch(request, *args, **kwargs)

    def get_context_data(self):
        context = super(ReportPageMixinPrep, self).get_context_data()
        context['report_page'] = self.report_page
        return context


class ReportPageMixin(ReportMixin, ReportPageMixinPrep):
    # It is done this way to ensure that the link report_page and report is confirmed before anything else is done
    pass


class ReportPageInfoView(ReportPageMixin, TemplateView):
    template_name = "reports/reportpage_detail.html"


class ReportPageUpdateView(ReportMixin, UpdateView):
    model = ReportPage
    fields = ['name', 'description', 'page_number']
    pk_url_kwarg = "report_page_id"
    template_name_field = "report_page"

    def get_success_url(self):
        url_kwargs = {
            'report_slug': self.report.slug,
            'report_page_id': self.object.id
        }
        return reverse("setup:reports:details", kwargs=url_kwargs)


class PDFTemplateView(TemplateResponseMixin, ContextMixin, View):
    """A view that adjusts the templatemixin to display the template in PDF form.
    It overrides all code from TemplateView class, thus does not inherit from it directly """
    template_engine = "PDFTemplates"
    response_class = PDFResponse
    file_name = 'test_file'

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
        orientation = 'Portrait' if self.report_page.report.display_options.orientation else 'Landscape'

        options.update({
            'page-size': self.report_page.report.display_options.size,
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


class PrintReportAsHTMLView(ReportMixin, TemplateView):
    template_name = "reports/pdf_report.html"
    template_engine = "PDFTemplates"

    def get_context_data(self):
        context = super(PrintReportAsHTMLView, self).get_context_data()
        context['pages'] = self.report.get_pages()
        return context