from django.template.loader import get_template


class BasePageRenderer:
    template_name = "pagedisplay/modules/page.html"

    replaced_module_widgets = []

    def __init__(self, page=None):
        self.page = page

    def render(self, request=None, **kwargs):
        """
        Render the modules inside the container in a vertical manner
        :param request: The Request object
        :param kwargs: Other kwarg arguments that can be used somewhere in the render process (= contents of context)
        :return:
        """
        # Get the template
        template = get_template(self.template_name, using=kwargs.get('template_engine', None))

        # Get the context
        context = self.get_context_data(request=request, **kwargs)
        # Renders the template with the context data.
        return template.render(context)

    def get_context_data(self, request=None, **kwargs):
        context = {'request': request,
                   'page': self.page,
                   'renderer': self,
                   'current_container': self,
                   }
        context.update(kwargs)
        return context

    @property
    def replaced_widgets_dict(self):
        """ Construct a dictionairy of modules with theire altered widgets """
        dict = {}
        for couple in self.replaced_module_widgets:
            if isinstance(couple[0], str):
                # The name of the module is given, instead of the class
                dict[couple[0]] = couple[1]
            else:
                # Assume a class is given directly instead of the name
                dict[couple[0].__name__] = couple[1]
        return dict