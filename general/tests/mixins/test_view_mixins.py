from django.views.generic import TemplateView
from django.test import Client
from django.urls import reverse
from django.test.client import RequestFactory
from django.contrib.auth.models import User


__all__ = ['ViewTestMixin', 'ViewMixinTestMixin', 'assertEqualInMultidict']


def assertEqualInMultidict(dict, lookup, compare_to, msg=None):
    lookups = lookup.split('.')
    cur_dict = dict
    found_lookup = ''
    for lookup_part in lookups:
        try:
            cur_dict = cur_dict.get(lookup_part)
        except KeyError:
            raise AssertionError(f"{lookup_part} in dict did not exist at {found_lookup}")
        found_lookup += '.' + lookup_part

    if cur_dict != compare_to:
        if msg is None:
            msg = f"instance at {lookup} was not {compare_to} but {cur_dict} instead"
        raise AssertionError(msg)


class ViewTestMixin:
    default_url_name = None
    default_url_kwargs = None
    url_namespace_prefix = ""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(username='new_user', is_superuser=True)
        self.client.force_login(self.user)
        super(ViewTestMixin, self).setUp()

    def build_url(self, url_name=None, url_kwargs=None):
        if url_name is None:
            url_name = self.default_url_name
        if url_kwargs is None:
            url_kwargs = self.default_url_kwargs
        return reverse(self.url_namespace_prefix+url_name, kwargs=url_kwargs)

    def build_get_response(self, url_name=None, url_kwargs=None, follow=False):
        return self._build_response(
            "get",
            url_name=url_name,
            url_kwargs=url_kwargs,
            follow=follow
        )

    def build_post_response(self, data, url_name=None, url_kwargs=None, follow=False):
        return self._build_response(
            "post",
            url_name=url_name,
            url_kwargs=url_kwargs,
            follow=follow,
            data=data
        )

    def _build_response(self, method, url_name=None, url_kwargs=None, client=None, follow=False, data={}):
        url = self.build_url(url_name, url_kwargs)
        client = client or self.client
        return getattr(client, method)(url, data=data, follow=follow)

    @staticmethod
    def assertHasMessage(response, level=None, text=None, print_all=False):
        """
        Assert that the response contains a specific message
        :param response: The response object
        :param level: The level of the message (messages.SUCCESS/ EROOR or custom...)
        :param text: (part of) the message string that it should contain
        :param print_all: prints all messages encountered useful to trace errors if present
        :return: Raises AssertionError if not asserted
        """
        for message in response.context['messages']:
            if print_all:
                print(message)
            if message.level == level or level is None:
                if text is None or str(text) in message.message:
                    return

        if level or text:
            msg = "There was no message for the given criteria: "
            if level:
                msg += f"level: '{level}' "
            if text:
                msg += f"text: '{text}' "
        else:
            msg = "There was no message"

        raise AssertionError(msg)

    def assertRequiresPermission(self, url_name=None, url_kwargs=None, permission=None):
        """ Assert that the given url requires a certain permission to visit """
        # Todo: not yet verified
        client = Client()
        user = User.objects.create(username=f'test_user_{permission}')
        client.force_login(self.user)

        response = self.build_get_response(url_name, url_kwargs, follow=False)
        self.assertEqual(response.status_code, 403)

        user.user_permissions.add(permission)
        response = self.build_get_response(url_name, url_kwargs, follow=False)
        self.assertEqual(response.status_code, 200)

    def assertIsSubclass(self, cls, parent):
        """ Assert that class is a subclass of parent """
        if not issubclass(cls, parent):
            raise AssertionError(f"{cls} does not inherit class {parent}")

    def assertInContext(self, response, key, instance=None):
        """ Assert if the given instance is in the response context.
        If no instance is given, search presence of key only """
        if instance is None:
            self.assertIn(key, response.context.keys())
        else:
            self.assertEqual(response.context[key], instance)


class ViewMixinTestMixin:
    """ Testclass designed to check functionality on view mixin classes by creating a new basic view class """
    view_mixin_class = None

    def setUp(self):
        # Create a request factory
        self.factory = RequestFactory()

    def get_view_class(self, url='', url_kwargs=None):
        url_kwargs = url_kwargs or {}

        # Create a get method that doesn't do anything
        def get(self, *args, **kwargs):
            return None

        # Create the class and the subsequent instance
        mixin_classes = self.view_mixin_class if isinstance(self.view_mixin_class, list) else [self.view_mixin_class]

        view_class = type("SpecialTestClass", (*mixin_classes, TemplateView), {'get': get})
        view_obj = view_class()
        request = self.factory.get(url)
        request.user = User.objects.create(username='admin_user_mixin_tester', is_superuser=True)

        view_obj.setup(request, **url_kwargs)
        view_obj.dispatch(request, **url_kwargs)
        return view_obj