from django import template
from ..models import Subject

register = template.Library()

@register.filter
def get_by_id(queryset, id):
    try:
        return queryset.get(id=id)
    except Subject.DoesNotExist:
        return None