from django.conf.urls import *
from django.views.generic import TemplateView
from yoloify.signup import views
from yoloify.signup.forms import LoginForm, PasswordChangeForm

urlpatterns = patterns('',
    # Logging in/out
    url(r'^login/$', 'django.contrib.auth.views.login', {
        'template_name': 'signup/login.html',
        'authentication_form': LoginForm
    }, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),

    # Signup
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^signup/done/$', TemplateView.as_view(template_name="signup/signup_done.html"), name='signup_done'),
    # Email confirmation
    url(r'^resend/$', views.confirmation_resend, name='confirmation_resend'),
    url(r'^confirm/(?P<username>[_\w.]{1,30})/(?P<key>\w{40})/$', views.confirm_email, name='confirm_email'),

    # Password reset
    url(r'^reset/$', views.reset_password, name='reset_password'),
    url(r'^reset/sent/$', TemplateView.as_view(template_name='signup/password_reset_sent.html'), name='reset_password_sent'),
    url(r'^reset/(?P<username>[_\w.]{1,30})/(?P<key>\w{40})/$', views.reset_password_confirm, name='reset_password_confirm'),
    url(r'^reset/done/$', TemplateView.as_view(template_name='signup/password_reset_done.html'), name='reset_password_done'),

    # Password change
    url(r'^password_change/$', 'django.contrib.auth.views.password_change', {
        'template_name': 'signup/password_change.html',
        'password_change_form': PasswordChangeForm
    }, name='change_password'),
    url(r'^password_change/done/$', 'django.contrib.auth.views.password_change_done', {'template_name': 'signup/password_change_done.html'}, name='change_password_done'),

    url(r'^settings/$', views.account_settings, name='settings'),

    url(r'^friends/$', views.friends, name='friends'),

    url('', include('social.apps.django_app.urls', namespace='social')),

    url(r'^checksocialuser/(?P<provider>\w+)/(?P<user_id>\d+)/$', views.check_social_user, name="check-social-user"),
)
