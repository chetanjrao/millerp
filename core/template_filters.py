from django.template.defaulttags import register

@register.filter
def hash(h, key):
    return h[key]


@register.filter
def indexing(h, index):
    return h[index]