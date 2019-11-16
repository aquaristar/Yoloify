from django.contrib.auth import authenticate, get_backends
from django_webtest import WebTest
from django.contrib.auth.models import User
from django.core import mail
import re

class LoginTest(WebTest):
    fixtures = ['test_users']
    setup_auth = False

    def test_normal(self):
        login = self.app.get('/login/')
        login_form = login.forms['login_form']
        login_form['email'] = 'aleks.selivanov@yahoo.com'
        login_form['password'] = '123'
        home = login_form.submit().follow() # -> Home
        self.assertTemplateUsed(home, 'pages/home.html')
        self.assertTemplateNotUsed(home, 'signup/login.html')

    """
    def test_from_homepage(self):
        home = self.app.get('/')
        login_form = home.forms['login-form']
        login_form['username'] = 'aleks'
        login_form['password'] = '123'
        home = login_form.submit().follow()
        self.assertTemplateNotUsed(home, 'signup/login.html')
        self.assertTemplateUsed(home, 'pages/home.html')
    """

    def test_wrong_pair(self):
        login = self.app.get('/login/')
        login_form = login.forms['login_form']
        login_form['email'] = 'wrong'
        login_form['password'] = 'wrong'
        response = login_form.submit()
        self.assertTemplateUsed(response, 'signup/login.html')


class SignupTest(WebTest):
    fixtures = ['test_users']

    re_confirmation_link = re.compile(r'https?://.+?(/confirm/4/\w+/)')

    def test_normal(self):
        home = self.app.get('/')
        signup = home.click('Sign Up', index=0)

        # Filling the signup form
        form = signup.forms['signup_form']
        form['first_name'] = 'Bill'
        form['last_name'] = 'Gates'
        form['email'] = 'bill@microsoft.com'
        form['password'] = '123'

        # Check e-mail
        assert len(mail.outbox) == 1
        email = mail.outbox[0]

        # Extract confirmation link
        match = self.re_confirmation_link.search(email.body)
        confirmation_url = match.group(1)

        # Click on confirmation link
        home = self.app.get(confirmation_url).follow()
        self.assertTemplateUsed(home, 'pages/home.html')
        assert 'Bill' in home

        # Sign out
        home.click('Sign Out').follow()

        # Try to use the confirmation link second time
        invalid = self.app.get(confirmation_url)
        self.assertTemplateUsed(invalid, 'signup/confirmation_invalid.html')

    def test_email_is_taken(self):
        signup = self.app.get('/signup/')
        form = signup.forms['signup_form']
        form['email'] = 'aleks.selivanov@yahoo.com'
        form['password'] = '123'
        signup = form.submit()
        assert 'This email address is already in use.' in signup

    def test_already_confirmed(self):
        invalid = self.app.get('/confirm/1/c9d86688966142b2295fa393f9608f8f21155d3f/')
        self.assertTemplateUsed(invalid, 'signup/confirmation_invalid.html')

    def test_invalid_confirmation(self):
        invalid = self.app.get('/confirm/1/c9d86688966142b2295fa393f9608f8f21155d3f/')
        self.assertTemplateUsed(invalid, 'signup/confirmation_invalid.html')

    def test_confirmation_resend(self):
        home = self.app.get('/')
        signup = home.click('Sign Up', index=0)

        # Filling the signup form
        form = signup.forms['signup_form']
        form['first_name'] = 'Bill'
        form['last_name'] = 'Gates'
        form['email'] = 'bill@microsoft.com'
        form['password'] = '123'

        signup = self.app.get('/signup/')
        resend = signup.click(href='/resend/')
        form = resend.forms['confirmation_resend_form']
        form['email'] = 'bill@microsoft.com'

        assert len(mail.outbox) == 2

    def test_confirmation_resend_already_confirmed(self):
        resend = self.app.get('/resend/')
        form = resend.forms['confirmation_resend_form']
        form['email'] = 'aleks.selivanov@yahoo.com'
        resend = form.submit()
        assert 'Email address is already confirmed.' in resend
        self.assertTemplateUsed(resend, 'signup/confirmation_resend.html')

    def test_confirmation_resend_invalid_key(self):
        resend = self.app.get('/resend/')
        form = resend.forms['confirmation_resend_form']
        form['email'] = 'invalid@yoloify.com'
        resend = form.submit()
        assert 'There is no user with the given e-mail address.' in resend
        self.assertTemplateUsed(resend, 'signup/confirmation_resend.html')


class PasswordChangeTest(WebTest):
    fixtures = ['test_users']
    setup_auth = False

    def test_normal(self):
        login = self.app.get('/login/')
        login_form = login.forms['login_form']
        login_form['email'] = 'aleks.selivanov@yahoo.com'
        login_form['password'] = '123'
        home = login_form.submit().follow() # -> Home
        password_change = home.click('Change Password')
        form = password_change.forms['password_change_form']
        form['old_password'] = '123'
        form['new_password1'] = '1234'
        form['new_password2'] = '1234'
        changed = form.submit().follow()
        self.assertTemplateUsed(changed, 'signup/password_change_done.html')

        home = changed.click('Sign Out').follow()
        login = self.app.get('/login/')
        login_form = login.forms['login_form']
        login_form['email'] = 'aleks.selivanov@yahoo.com'
        login_form['password'] = '1234'
        home = login_form.submit().follow() # -> Home
        self.assertTemplateUsed(home, 'pages/home.html')
        self.assertTemplateNotUsed(home, 'signup/login.html')