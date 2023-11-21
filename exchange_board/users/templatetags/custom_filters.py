from django import template

register = template.Library()


@register.filter(name='intspace')
def intspace(value):
    try:
        formatted_value = '{:,.2f}'.format(value).replace(",", " ")
        if formatted_value.endswith('.00'):
            return formatted_value[:-3]
        return formatted_value
    except:
        return value


@register.filter(name='range')
def filter_range(start, end):
    return range(start, end)
