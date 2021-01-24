from importlib import import_module

from django.apps import apps


class SetupConfig:
    name = None
    url_keyword = None
    namespace = None

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
        return None




def get_all_configs():
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
                        configs.append(cls())
    return configs