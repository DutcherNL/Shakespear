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
        return value.slug