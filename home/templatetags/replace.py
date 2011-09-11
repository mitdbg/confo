from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def expandcommas(value):
    return value.replace(',',', ')




@register.filter
def filterstr(value, badword=None):
    return filter(lambda w: w != badword, value)
