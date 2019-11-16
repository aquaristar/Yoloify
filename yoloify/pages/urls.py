from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from yoloify.pages import views


urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^fb/$', views.fb_home, name='fb'),
    url(r'^about/$', views.about, name='about'),
    url(r'^pages/(?P<slug>[a-z-]*)/$', views.page, name='static-page'),
    url(r'^test/$', TemplateView.as_view(template_name='pages/test.html'), name='test'),

    url(r'^divide_by_zero_please/$', views.divide_by_zero) # to test 500 error handler
)