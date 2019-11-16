from django.conf.urls import *

urlpatterns = patterns(
    'yoloify.stats.views',
    url(r'^usage/daily/$', 'usage_stats_daily', name='usage_stats_daily'),
    url(r'^usage/total/$', 'usage_stats_total', name='usage_stats_total'),
    #temp
    url(r'^usage/start_task/$', 'usage_start_task'),
)
