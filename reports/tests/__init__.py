import os
import shutil

from django.test import override_settings
from django.conf import settings


def create_overwrite_media_folder_decorator(module_name):
    """ Returns a class mixin that moves the media folder to the tests/files folder in the given module.
    Used when filefield contains physical documents. """
    media_folder = os.path.join(settings.BASE_DIR, module_name, 'tests', 'files')

    class UseTestMediaRootMixin(override_settings):

        def __init__(self, **kwargs):
            kwargs.update({
                'MEDIA_ROOT': media_folder,
            })
            super(UseTestMediaRootMixin, self).__init__(**kwargs)

        def decorate_class(self, cls):
            super(UseTestMediaRootMixin, self).decorate_class(cls)

            decorated_tearDownClass = cls.tearDownClass
            def tearDownClass():
                # Clear the new media folder contents, otherwise data will keep growing each test run.
                try:
                    shutil.rmtree(os.path.join(media_folder, module_name))
                except FileNotFoundError:
                    # FileField was not processed like this
                    pass
                decorated_tearDownClass()

            cls.tearDownClass = tearDownClass
            return cls
    return UseTestMediaRootMixin
