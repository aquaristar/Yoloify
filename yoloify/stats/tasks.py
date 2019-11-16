import datetime
from django.contrib import comments
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from celery import shared_task
from celery import task

from yoloify.pinboard.models import Goal, Pin
from yoloify.stats.models import UsageStatsDaily
from yoloify.signup.models import Profile


def get_comments(timestamp):
    #get comment count
    CommentModel = comments.get_model()
    ctype = ContentType.objects.get_by_natural_key('pinboard', 'goal')
    qs = CommentModel.objects.filter(
        content_type=ctype,
        site__pk=settings.SITE_ID,
        submit_date__startswith=timestamp
    )
    return qs


@shared_task
def aggregate_daily_goals_pins(usage_id):
    usage = UsageStatsDaily.objects.get(id=usage_id)
    #Newly created goals
    goals = Goal.objects.filter(created__startswith=usage.usage_date)
    usage.total_location_pin = goals.filter(pin_type='location').count()
    #Total repins
    repins = Pin.objects.filter(created_at__startswith=usage.usage_date)
    location_repins = repins.filter(goal__pin_type='location').count()
    usage.total_location_repin = abs(location_repins - usage.total_location_pin)
    usage.save()


@shared_task
def aggregate_daily_action_stats(usage_id):
    usage = UsageStatsDaily.objects.get(id=usage_id)
    #Total complete pins
    complete_pins = Pin.objects.filter(complete=True, complete_at__startswith=usage.usage_date)
    usage.total_location_completed = complete_pins.filter(goal__pin_type='location').count()
    #Total comments
    usage.total_comments = get_comments(usage.usage_date).count()
    usage.save()


@shared_task
def aggregate_daily_usage_stats(usage_date=None):
    """
    aggregate daily usage stats
    """
    usage_date = usage_date or timezone.now().date()
    usage, created = UsageStatsDaily.objects.get_or_create(usage_date=usage_date)
    #Total created users
    usage.total_new_users = User.objects.filter(date_joined__startswith=usage_date).count()
    #Total active users
    usage.total_active_users = Profile.objects.filter(last_activity__startswith=usage_date).count()
    usage.save()
    aggregate_daily_goals_pins.apply_async(args=(usage.id, ), queue='default-queue')
    aggregate_daily_action_stats.apply_async(args=(usage.id, ), queue='default-queue')


@task
def aggregate_usage_stats():
    today = timezone.now().date()
    users = User.objects.all().order_by('date_joined')
    if not users:
        return
    day = users[0].date_joined.date()
    while day <= today:
        aggregate_daily_usage_stats(day)
        day = day + datetime.timedelta(days=1)
