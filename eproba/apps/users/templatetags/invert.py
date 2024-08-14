from django import template

register = template.Library()


@register.filter
def invert(value):
    return not value
