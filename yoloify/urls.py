from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
import time
from django.views.generic import TemplateView
from django.views.static import serve
from yoloify import api
from yoloify.api import PasswordChangeView, PasswordResetView, LoginView, SignupView, ImageUploadView, \
    ConfirmationResendView, LikeView, ContactView, CommentView, CommentFlagView, BookmarkView, CompletedView
import sitemaps

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': {
        'pages': sitemaps.PagesSitemap,
        'pin': sitemaps.PinSitemap,
        'profile': sitemaps.ProfileSitemap,
        'city': sitemaps.CitySitemap,
        'CityCategory': sitemaps.CityCategorySitemap,
        'CityGetawayList': sitemaps.CityGetawayListSitemap,
        'CityGetaway': sitemaps.CityGetawaySitemap,

    }}, name='django.contrib.sitemaps.views.sitemap'),

    (r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),

    url(r'^', include('yoloify.pages.urls')),
    url(r'^', include('yoloify.signup.urls')),
    url(r'^', include('yoloify.pinboard.urls')),

    url(r'^stats/', include('yoloify.stats.urls')),
    url(r'^cpanel/', include('yoloify.cpanel.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^api/', include(api.router.urls)),
    url(r'^api/change_password', PasswordChangeView.as_view(), name='api-change-password'),
    url(r'^api/reset_password', PasswordResetView.as_view(), name='api-reset-password'),
    url(r'^api/login', LoginView.as_view(), name='api-login'),
    url(r'^api/signup', SignupView.as_view(), name='api-signup'),
    url(r'^api/upload', ImageUploadView.as_view(), name='api-upload'),
    url(r'^api/resend', ConfirmationResendView.as_view(), name='api-resend'),
    url(r'^api/like/', LikeView.as_view(), name='api-like'),
    url(r'^api/bookmark/', BookmarkView.as_view(), name='api-bookmark'),
    url(r'^api/complete/', CompletedView.as_view(), name='api-complete'),
    url(r'^api/contact', ContactView.as_view(), name='api-contact'),
    url(r'^api/comments', CommentView.as_view(), name='api-comment'),
    url(r'^api/commentflag', CommentFlagView.as_view(), name='api-comment-flag'),

    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^(?P<username>[\w0-9_]+)/$', 'yoloify.pinboard.views.profile_by_username', name='profile-by-username'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^favicon.ico$', 'django.views.static.serve', {
            'document_root': settings.STATICFILES_DIRS[0], # global static dir
            'path': 'favicon.ico'
        }),
    )

def myserve(request, path, document_root=None, show_indexes=False):
    time.sleep(2)
    response = serve(request, path, document_root, show_indexes)
    response['Cache-Control'] = 'no-cache'
    del response['Last-Modified']
    return response

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, view=myserve, document_root=settings.MEDIA_ROOT)
