from django import template

register = template.Library()

@register.assignment_tag(takes_context=True)
def is_reposted(context, pin):
    user = context['user']
    if user.is_authenticated():
        return pin.is_reposted_by(user)
    return False