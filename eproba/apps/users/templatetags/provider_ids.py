from django import template

register = template.Library()


@register.filter
def ids(value: dict):
    output = []
    for item in value:
        output.append(item.id)
    return output
