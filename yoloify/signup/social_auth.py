from requests import request, HTTPError
from django.core.files.base import ContentFile
from django.conf import settings
from yoloify.signup.models import Profile
from yoloify.signup.views import follow_facebook_friends
from yoloify.utils.views import send_signup_admin_notification


def create_profile(*args, **kwargs):
    if kwargs.get("is_new"):
        user = kwargs.get("user")
        Profile.objects.create(user=user, is_signup_finished=False)


def user_details(backend, details, response, user=None, *args, **kwargs):
    """Update user details using data from provider."""
    if user:
        changed = False  # flag to track changes
        protected = backend.setting('PROTECTED_USER_FIELDS', []) if not kwargs.get("is_new") else []
        keep = ('username', 'id', 'pk') + tuple(protected)

        for name, value in details.items():
            # do not update username, it was already generated
            # do not update configured fields if user already existed
            if name not in keep and hasattr(user, name):
                if value and value != getattr(user, name, None):
                    try:
                        setattr(user, name, value)
                        changed = True
                    except AttributeError:
                        pass

       
            
    if kwargs.get("is_new") and backend.name == 'facebook':
        follow_facebook_friends(user)
        if getattr(settings, 'ADMIN_SIGNUP_NOTIFICATION', False) and user:
            send_signup_admin_notification(user)


def save_profile_picture(backend, user, response, is_new=False, *args, **kwargs):
    if is_new and backend.name == 'facebook':
        url = 'http://graph.facebook.com/{0}/picture'.format(response['id'])
        try:
            response = request('GET', url, params={'type': 'large'})
            response.raise_for_status()
        except HTTPError:
            pass

        profile = user.get_profile()
        profile.userpic.save('{0}_social.jpg'.format(user.username), ContentFile(response.content))
        profile.save()