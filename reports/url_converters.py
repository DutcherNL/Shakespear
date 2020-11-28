from reports.models import PageLayout


class PageLayoutConverter:
    regex = '[^/]+'

    # Uses slug as identifier

    def to_python(self, value):
        try:
            return PageLayout.objects.get(slug=value)
        except PageLayout.DoesNotExist:
            raise ValueError("No match found for {0}".format(value))

    def to_url(self, value):
        """ Converts a Pagelayout instance to the relevant url, can also take the Pagelayout id instead """
        # Intercept integer as object id and get the related object
        if isinstance(value, int):
            value = PageLayout.objects.get(id=value)

        return value.slug