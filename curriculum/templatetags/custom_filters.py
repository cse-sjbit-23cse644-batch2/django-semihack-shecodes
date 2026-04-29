from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return {}
    return dictionary.get(key, {})

@register.filter
def split(value, arg):
    if not value:
        return []
    return value.split(arg)

@register.filter
def add(value, arg):
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value