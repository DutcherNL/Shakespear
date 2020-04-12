import math

from django.core.paginator import Paginator, Page


class FlexPage(Page):

    def get_option_range(self):
        pos_left = self.number - self.paginator.flex_range
        pos_right = self.number + self.paginator.flex_range - min(0, pos_left)
        pos_left = max(1, pos_left)
        pos_right = min(pos_right, self.paginator.num_pages)

        return range(pos_left, pos_right+1)


class FlexPaginator(Paginator):
    flex_range = 3

    def _get_page(self, *args, **kwargs):
        """
        Overwrite the page instances
        """
        return FlexPage(*args, **kwargs)


class FlexPaginationMixin:
    paginator_class = FlexPaginator