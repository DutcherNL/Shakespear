from functools import update_wrapper
from importlib import import_module

from django.apps import apps
from django.http import HttpResponseForbidden
from django.urls import reverse


class SetupConfig:
    name = None
    url_keyword = None
    namespace = None
    root_url_name = None

    access_required_permissions = []

    button = {
        'class': 'btn-primary',
        'image': None,
    }

    def __init__(self):
        # Set the button default values in case a new dict was defined
        for key, value in SetupConfig.button.items():
            self.button.setdefault(key, value)

    def get_urls(self):
        """ Builds a list of urls """
        raise NotImplementedError

    @property
    def urls(self):
        return self.get_urls(), self.namespace, self.namespace

    @property
    def root_url(self):
        return self.get_root_url()

    def get_root_url(self):
        url_pattern = 'setup'
        if self.namespace:
            url_pattern += ':'+self.namespace
        url_pattern += ':home' if self.root_url_name is None else f':{self.root_url_name}'

        return reverse(url_pattern)

    @staticmethod
    def _check_is_logged_in(request):
        return request.user.is_authenticated

    def _check_permissions(self, request):
        """ Check if the given users has all required permissions """
        for perm in self.access_required_permissions:
            print(f'check perm for {perm}')
            if not request.user.has_perm(perm):
                print('not present')
                return False
        return True

    def check_access(self, request):
        if not self._check_is_logged_in:
            return False

        if not self._check_permissions(request):
            return False

        return True

    def limit_access(self, view_method):
        """ A wrapper around view methods (or class.as_views()) that halts access for anyone not authorised.
        Useful here to limit continuous wrapping around each view."""
        def wrapper(request, *args, **kwargs):
            # Construct the view
            if self.check_access(request):
                return view_method(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("Je hebt geen rechten voor deze pagina")

        return update_wrapper(wrapper, view_method)




def get_all_configs(request=None):
    """ Returns a list of all setup configs used by this application"""
    configs = []

    for app in apps.get_app_configs():
        try:
            module = import_module(f'{app.name}.setup.config')
        except ModuleNotFoundError:
            pass
        else:
            for name, cls in module.__dict__.items():
                if isinstance(cls, type):
                    # Get all subclasses of SetupConfig, but not accidental imported copies of SetupConfig
                    if issubclass(cls, SetupConfig) and cls != SetupConfig:
                        config = cls()
                        if request:
                            if config.check_access(request=request):
                                configs.append(config)
                        else:
                            # There is no request, so no filter. Display all possible configs.
                            configs.append(config)
    return configs