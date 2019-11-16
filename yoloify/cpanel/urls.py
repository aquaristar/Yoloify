from django.conf.urls import *

urlpatterns = patterns(
    'yoloify.cpanel.views',
    url(r'^$', 'index', name='cpanel-home'),
)
