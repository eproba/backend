from django import template

register = template.Library()


@register.filter
def replace_stars(value):
    """
    Replacing stars in the string with *. It speeds up the rendering of the PDF.
    """
    return value.replace("⭐", "*")
