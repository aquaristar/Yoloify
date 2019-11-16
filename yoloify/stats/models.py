from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from collections import Counter


class UsageStatsDaily(models.Model):
    """
    Usage Stats daily
    """
    usage_date = models.DateField(_('Day'))
    total_location_pin = models.PositiveIntegerField(_('Location Pins'), default=0)
    total_location_repin = models.PositiveIntegerField(_('Location Repins'), default=0)
    total_location_completed = models.PositiveIntegerField(_('Location Completed'), default=0)
    total_likes = models.PositiveIntegerField(_('Likes'), default=0)
    total_comments = models.PositiveIntegerField(_('Comments'), default=0)
    total_new_users = models.PositiveIntegerField(_('New Users'), default=0)
    total_active_users = models.PositiveIntegerField(_('Active Users'), default=0)

    class Meta:
        ordering = ('usage_date', )

    def __unicode__(self):
        return u'Usage stats at {0}'.format(self.usage_date)

    def get_dict(self, exclude=None):
        exclude_fields = exclude or ('id', )
        _dict = {}

        for field in self._meta.fields:
            fname = field.name
            if fname not in exclude_fields:
                _dict[fname] = getattr(self, fname)

        return _dict

    @staticmethod
    def get_usage_stats(start, end):
        usage = UsageStatsDaily.objects.all()

        if start and not end:
            end = timezone.now().date()

        if start and end:
            usage = usage.filter(
                usage_date__gte=start,
                usage_date__lte=end
            )

        return usage

    @staticmethod
    def usage_stats_daily(start=None, end=None):
        usage = UsageStatsDaily.get_usage_stats(start, end)

        response_data = []
        for stat in usage:
            response_data.append(stat.get_dict())

        return response_data

    @staticmethod
    def usage_stats_total(start=None, end=None):
        usage = UsageStatsDaily.get_usage_stats(start, end)

        response_data = Counter({
            'total_location_pin': 0,
            'total_location_repin': 0,
            'total_location_completed': 0,
            'total_likes': 0,
            'total_comments': 0,
            'total_new_users': 0,
            'total_active_users': 0
        })

        for stat in usage:
            for key in stat.get_dict(exclude=('usage_date', 'id')):
                response_data[key] += getattr(stat, key)

        return response_data
