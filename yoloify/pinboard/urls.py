from django.conf.urls import *
from yoloify.pinboard import views

urlpatterns = patterns('',
    url(r'^newsfeed/$', views.newsfeed, name='newsfeed'),
    url(r'^trending/$', views.trending, name='trending'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^profile/(?P<profile_id>\d+)/$', views.profile, name='profile'),
    url(r'^board/(?P<username>[\w0-9_]+)/$', views.profile_by_username, name='profile_by_username'),
    url(r'^pin/$', views.CreateNewPinView.as_view(), name='create_pin'),
    url(r'^pin/(?P<pk>\d+)/(?P<slug>[\w-]+)/$', views.pin, name='pin'),
    url(r'^follow/(?P<profile_id>\d+)/$', views.follow, name='follow'),
    url(r'^unfollow/(?P<profile_id>\d+)/$', views.unfollow, name='unfollow'),
    url(r'^map/markers/$', views.map_markers, name='map_markers'),
    url(r'^next-part/(?P<pinboard_name>\w+)/$', views.next_part, name='pinboard_next_part'),
    url(r'^local/$', views.local, name='local'),
    url(r'^local/(?P<city_id>\d+)/things-to-do-in-(?P<city_name>[\w-]+)/$', views.city, name='city'),
    url(r'^local/(?P<city_getawaylist_id>\d+)/weekend-getaways-from-(?P<city_name>[\w-]+)/$', views.city_getawaylist, name='city_getawaylist'),
    url(r'^local/(?P<city_cat_id>\d+)/(?P<cat_name>[\w-]+)-near-(?P<city_name>[\w-]+)/$', views.city_category, name='city_category'),
    url(r'^local/(?P<city_getaway_id>\d+)/getaway-from-(?P<city_name>[\w-]+)-to-(?P<getaway_name>[\w-]+)/$', views.city_getaway, name='city_getaway'),
    url(r'^map/list/$', views.map_list, name='map_list'),
    url(r'^map/$', views.map, name='map'),
    url(r'^search/$', views.search, name='search')

)
