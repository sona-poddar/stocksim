
from django import template


register = template.Library()

@register.filter
def sub(value, arg):
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg) if arg != 0 else ''
    except (ValueError, TypeError):
        return ''

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)