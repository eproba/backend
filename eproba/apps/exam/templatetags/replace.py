from django import template

register = template.Library()


@register.filter
def replace_stars(value):
    """
    Replacing stars in the string with *.
    """
    return value.replace("⭐", "*")
