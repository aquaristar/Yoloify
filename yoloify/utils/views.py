import json
import decimal
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings


class LoginRequiredMixin(object):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


def json_date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def send_signup_admin_notification(user):
        'It sends email to admin when new user registers'
        subject = "New SignUp! YOLOify"
        context = {
            'name': "%s %s" % (user.first_name, user.last_name),
            'email': user.email,
            'id': user.id
        }
        message = render_to_string('emails/new_signup_admin_notification.txt', context)
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, settings.ADMINS)
        except Exception, ex:
            print ex
            pass


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):  # handles both date and datetime objects
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            return json.JSONEncoder.default(self, obj)
        
        
def break_down_phone_number(phone_number):
    """
    >>> break_down_phone_number('(111) 111-1111')
    ('111', '111', '1111')
    >>> break_down_phone_number('2222222222')
    ('222', '222', '2222')
    >>> break_down_phone_number('012345678901')
    >>> break_down_phone_number('(1111) 1112-1111')
    >>> break_down_phone_number('abcdedefg12334')
    """
    import re
    number = re.sub(r'[^\d]', '', phone_number)
    if len(number) == 10:
        return number[:3], number[3:6], number[6:]

if __name__ == "__main__":
    import doctest
    doctest.testmod()
