from datetime import timedelta

from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def filter_recent(interest_queryset, days):
    date_threshold = timezone.now() - timedelta(days=days)
    return interest_queryset.filter(last_updated__gte=date_threshold)
