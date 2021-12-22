import platform

import django
from django import template

import scouts_exams

register = template.Library()


@register.simple_tag
def python_version():
    return platform.python_version()


@register.simple_tag
def django_version():
    return django.get_version()


@register.simple_tag
def app_version():
    return scouts_exams.__version__
