from django import template

register = template.Library()


@register.filter
def to_k(value):
    return f'{value//1000}k'


@register.filter
def range_filter(value):
    return range(1, value + 1)