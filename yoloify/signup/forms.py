from datetime import datetime
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Button
from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import MAXIMUM_PASSWORD_LENGTH
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm as authSetPasswordForm
from django.contrib.auth.forms import PasswordChangeForm as authPasswordChangeForm
from django.utils.translation import ugettext as _
from yoloify.signup.models import EmailConfirmation, PasswordReset, Profile
from yoloify.utils import total_minutes


# TODO get rid of helpers in __init__s


class SignupForm(forms.ModelForm):
    first_name = forms.CharField(label=_('First name'), max_length=30)
    last_name = forms.CharField(label=_('Last name'), max_length=30)
    email = forms.EmailField(label=_('Email address'))
    password = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput, max_length=MAXIMUM_PASSWORD_LENGTH)

    class Meta:
        model = User
        fields = ('first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'signup_form'
        self.helper.add_input(Submit('submit', 'Sign Up!'))

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('This email address is already in use. Please supply a different email address.'))
        return email

    MIN_LENGTH = 6

    def clean_password(self):
        password = self.cleaned_data.get('password')

        # At least MIN_LENGTH long
        if len(password) < self.MIN_LENGTH:
            raise forms.ValidationError(_("The password must be at least %d characters long." % self.MIN_LENGTH))
        
        return password

    def save(self):
        user = super(SignupForm, self).save(commit=False)
        user.username = 'YOLOify' # placehold until we got user's ID
        user.set_password(self.cleaned_data["password"])
        user.email = self.cleaned_data['email']
        # user.is_active = False
        user.save()
        user.username = str(user.id)
        user.save()
        Profile.objects.create(user=user)
        EmailConfirmation.objects.create(user=user)
        return user


# copy-pasted a lot from django.contrib.auth.forms.AuthenticationForm
class LoginForm(forms.Form):
    email = forms.EmailField(label=_('E-mail'), required=True)
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput,
        max_length=MAXIMUM_PASSWORD_LENGTH,
    )

    def __init__(self, request=None, *args, **kwargs):
        """
        If request is passed in, the form will validate that cookies are
        enabled. Note that the request (a HttpRequest object) must have set a
        cookie with the key TEST_COOKIE_NAME and value TEST_COOKIE_VALUE before
        running this validation.
        """
        self.request = request
        self.user_cache = None
        super(LoginForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_id = 'login_form'
        self.helper.add_input(Submit('submit', 'Sign In'))

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            username = ''
            try:
                user = User.objects.get(email=email)
                username = user.username
            except User.DoesNotExist:
                pass
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(_("Please enter a correct e-mail address and password."))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_("This account is inactive."))
        #self.check_for_test_cookie()
        return self.cleaned_data

    def check_for_test_cookie(self):
        if self.request and not self.request.session.test_cookie_worked():
            raise forms.ValidationError(_("Your Web browser doesn't appear to have cookies "
                                          "enabled. Cookies are required for logging in."))

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class ConfirmationResendForm(forms.Form):
    email = forms.EmailField(label=_('Email address'), max_length=75,
        widget=forms.TextInput(attrs={'size': 30}))

    def __init__(self, *args, **kwargs):
        super(ConfirmationResendForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'confirmation_resend_form'
        self.helper.add_input(Submit('submit', 'Resend confirmation'))

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email__iexact=email)
            if not hasattr(user, 'email_confirmation'):
                raise forms.ValidationError(_('Email address is already confirmed.'))
            self.user = user
        except User.DoesNotExist:
            raise forms.ValidationError(_('There is no user with the given e-mail address.'))
        return email

    def clean(self):
        if 'email' in self.cleaned_data:
            user = self.user
            last_sent = user.email_confirmation.last_sent
            from django.utils.timezone import utc
            now = datetime.utcnow().replace(tzinfo=utc)
            if last_sent is not None and total_minutes(now - last_sent) < settings.EMAIL_RESEND_INTERVAL:
                raise forms.ValidationError(_('You do that too often. Please try again later.'))
        return self.cleaned_data

    def save(self):
        self.user.email_confirmation.send()


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("Email address"), max_length=75, widget=forms.TextInput(attrs={'size':30}))

    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('reset', 'Send Reset Email'))

    def clean_email(self):
        """
        Validates that an active user exists with the given e-mail address.
        """
        email = self.cleaned_data["email"]
        try:
            self.user = User.objects.get(email__iexact=email, is_active=True)
        except User.DoesNotExist:
            raise forms.ValidationError(_("That email address doesn't have an associated user account."))
        return email

    def clean(self):
        self.cleaned_data = super(PasswordResetForm, self).clean()
        if 'email' in self.cleaned_data:
            user = self.user
            resets = user.password_resets.all()
            if resets.count() > 0:
                last_reset = resets.order_by('-last_sent')[0]
                from django.utils.timezone import utc
                now = datetime.utcnow().replace(tzinfo=utc)
                if last_reset is not None and total_minutes(now - last_reset.last_sent) < settings.EMAIL_RESEND_INTERVAL:
                    raise forms.ValidationError(_('You do that too often. Please try again later.'))
        return self.cleaned_data

    def save(self, domain_override=None, use_https=False):
        user = self.user
        reset = PasswordReset.objects.create(user=user)
        reset.send(use_https=use_https)
        return reset


class SetPasswordForm(authSetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(SetPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('set', 'Set New Password'))


class PasswordChangeForm(authPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'password_change_form'
        self.helper.add_input(Submit('set', 'Set New Password'))

        if self.user.password == '!':
            self.fields.pop('old_password')

    def clean_old_password(self):
        if self.user.password != '!':
            return super(PasswordChangeForm, self).clean_old_password()
            
    MIN_LENGTH = 6

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')

        # At least MIN_LENGTH long
        if len(password1) < self.MIN_LENGTH:
            raise forms.ValidationError(_("The new password must be at least %d characters long." % self.MIN_LENGTH))
        
        return password1


class SettingsForm(forms.ModelForm):
    username = forms.CharField(label=_('Username'), required=False, validators=Profile._meta.get_field('username').validators)
    email = forms.EmailField(label=_('Email address'), required=False)
    userpic = forms.ImageField(label=_('User picture'), required=False)
    about = forms.CharField(label=_('About'), widget=forms.Textarea, required=False)
    location = forms.CharField(label=_('Location'), required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super(SettingsForm, self).__init__(*args, **kwargs)
        site = Site.objects.get_current()
        self.fields['username'].help_text = mark_safe(_('This makes your profile accessible via http://%s/<strong>username</strong>') % site.domain)

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username:
            return None
        if Profile.objects.exclude(user=self.instance).filter(username=username).exists():
            raise forms.ValidationError(_('Sorry, but this username is already taken.'))
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError(_('This email address is already in use. Please supply a different email address.'))
        return email

    def save(self):
        user = super(SettingsForm, self).save(commit=True)
        try:
            profile = user.get_profile()
        except Profile.DoesNotExist:
            profile = Profile(user=user)
        if 'username' in self.cleaned_data:
            profile.username = self.cleaned_data['username']
        if 'userpic' in self.cleaned_data:
            profile.userpic = self.cleaned_data['userpic']
        if 'about' in self.cleaned_data:
            profile.about = self.cleaned_data['about']
        if 'location' in self.cleaned_data:
            profile.location = self.cleaned_data['location']
        if 'email' in self.cleaned_data:
            profile.email = self.cleaned_data['email']
            
        profile.save()
        return user
