from django.views.generic import View
from django.views.generic.edit import FormView
from django.http import HttpResponseForbidden, Http404
from django.shortcuts import render
from django.urls import reverse
from django.template.loader import get_template, TemplateDoesNotExist

from .forms import MailForm

class EmailTemplateView(View):
    """
    A view to test mail templates with.
    The contentfactory class inside ensures that when an object does not reside in the context,
    it prints the query name instead
    """

    class ContentFactory(dict):
        """
        A dictionary that either returns the content, or a new dictionary with the name of the searched content
        Used to replace unfound content in the template with the original name
        """
        def __init__(self, name="", dictionary={}):
            self._dict = dictionary
            self._name = name

        def __getattr__(self, key):
            return self[key]

        def __getitem__(self, key):
            item = self._dict.get(key, None)
            if item is None:
                return EmailTemplateView.create_new_factory(name="{name}.{key}".format(name=self._name, key=key))
            else:
                return item

        def __contains__(self, item):
            # All objects exist, either in the dictionary, or a new one is created
            return True

        def __str__(self):
            return "-{}-".format(self._name)

        def __repr__(self):
            return self._dict.__str__()

        def __setitem__(self, key, value):
            self._dict[key] = value

    @staticmethod
    def create_new_factory(name=""):
        return EmailTemplateView.ContentFactory(name=name)

    def get(self, request):
        if not request.user.is_superuser:
            return HttpResponseForbidden("You do not have permission to view this")

        template_location = request.GET.get('template', None) + ".html"

        try:
            template = get_template(template_location, using='EmailTemplates')
        except TemplateDoesNotExist:
            return Http404("Given template name not found")

        context = self.ContentFactory(dictionary=request.GET.dict())
        context['request'] = request
        context['user'] = request.user
        return render(None, template_location, context, using='EmailTemplates')


class ConstructMailView(FormView):
    template_name = "mailing/construct_mail.html"
    form_class = MailForm

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_email()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('construct')
