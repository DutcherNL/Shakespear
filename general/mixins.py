from urllib.parse import urlparse, urlunparse

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect, QueryDict, Http404
from django.utils.http import is_safe_url

from Questionaire.models import Inquirer


class AccessMixin:
    """ Checks whether the given inquirer has an e-mail registered, if not divert to email processing page
    This is inspired and mostly copied from Djangos contrib.auth.mixins.AccessMixin, however that particular one
    is designed for anything User related, which this one doesn't and could therefor fail when the Userclass is active
    """

    redirect_field_name = 'on_success'
    adress_issue_url = None

    def dispatch(self, request, *args, **kwargs):
        if not self.check_access_condition():
            return self.redirect_to_mail_confirmation_screen(request)
        else:
            return super(AccessMixin, self).dispatch(request, *args, **kwargs)

    def check_access_condition(self):
        """
        Checks the access condition, return false if access condition is not met (e.g. inquirer is not logged in)
        :return: Boolean
        """
        return True

    def get_issue_url(self):
        """ Returns the url to redirect to """
        if self.adress_issue_url is None:
            raise ImproperlyConfigured(
                '{0} is missing the adress_issue_url attribute. Define {0}.adress_issue_url, or override '
                '{0}.get_issue_url().'.format(self.__class__.__name__)
            )
        return str(self.adress_issue_url)

    def redirect_to_mail_confirmation_screen(self, request, redirect_field_name=None):
        """
        Redirect the user to the login page, passing the given 'next' page.
        """
        redirect_field_name = redirect_field_name or self.redirect_field_name
        next = request.build_absolute_uri()

        resolved_url = self.get_issue_url()

        # If the login url is the same scheme and net location then use the
        # path as the "next" url. This is copied from Djangos source code (LoginRequiredMixin.handle_no_permission()
        login_scheme, login_netloc = urlparse(resolved_url)[:2]
        current_scheme, current_netloc = urlparse(next)[:2]
        if (
                (not login_scheme or login_scheme == current_scheme) and
                (not login_netloc or login_netloc == current_netloc)
        ):
            next = self.request.get_full_path()

        url_parts = list(urlparse(resolved_url))
        if redirect_field_name:
            querystring = QueryDict(url_parts[4], mutable=True)
            querystring[redirect_field_name] = next
            url_parts[4] = querystring.urlencode(safe='/')

        return HttpResponseRedirect(urlunparse(url_parts))


class RedirectThroughUriOnSuccess:
    """ Overrides FormView get_success_url to redirect to the location defined in the url """
    redirect_field_name = 'on_success'

    def get_success_url(self, *args, **kwargs):
        """Return the user-originating redirect URL if it's safe."""
        redirect_to = self.request.POST.get(
            self.redirect_field_name,
            self.request.GET.get(self.redirect_field_name, '')
        )
        url_is_safe = is_safe_url(
            url=redirect_to,
            allowed_hosts=None,
            require_https=self.request.is_secure(),
        )
        if url_is_safe:
            return redirect_to
        else:
            return super(RedirectThroughUriOnSuccess, self).get_success_url(*args, **kwargs)


class InquiryMixin:
    """ Mixin that takes the inquirer and inquiry from the current session """
    raise_404_on_missing_inquirer = True

    def setup(self, request, *args, **kwargs):
        try:
            self.inquirer = Inquirer.objects.get(id=request.session.get('inquirer_id', None))
        except Inquirer.DoesNotExist:
            if self.raise_404_on_missing_inquirer:
                raise Http404("U heeft momenteel niet een actieve inquirer sessie")

        self.inquiry = self.inquirer.active_inquiry
        return super(InquiryMixin, self).setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InquiryMixin, self).get_context_data(**kwargs)
        context['inquiry'] = self.inquiry
        context['inquirer'] = self.inquirer
        return context

