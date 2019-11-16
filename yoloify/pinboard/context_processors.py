from crispy_forms.helper import FormHelper
from django.conf import settings
from django.contrib.sites.models import Site
from yoloify.pinboard.forms import NewGoalForm, NewLocationGoalForm, ContactForm


def pinboard_settings(request):
    newpin_form = NewLocationGoalForm()
    newpin_form.helper = FormHelper()
    newpin_form.helper.form_tag = False

    contact_form = ContactForm()
    contact_form.helper = FormHelper()
    contact_form.helper.form_tag = False

    return {
        'SITE_DOMAIN': Site.objects.get_current().domain,
        'newpin_shortcut': newpin_form,
        'contact_shortcut': contact_form,
        'PIN_THUMB_SIZE': settings.PIN_THUMB_SIZE,
        'PIN_SIZE': settings.PIN_SIZE,
        'UPLOAD_FILE_MAX_SIZE': settings.UPLOAD_FILE_MAX_SIZE,
        'SUPPORTED_IMAGE_FORMATS': settings.SUPPORTED_IMAGE_FORMATS,
    }
