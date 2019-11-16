from __future__ import absolute_import

import logging
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import get_cache
from django.contrib.auth.models import User
from django.db.models import F, Count
from django.db.models.signals import post_save
from django.contrib.gis.measure import D  # ``D`` is a shortcut for ``Distance``
from django.contrib.gis.geos import fromstr

from celery import shared_task
from haystack.query import SearchQuerySet
from redis import Redis

from yoloify.pinboard.models import Pin, Location, Goal, City, CityCategory, CityGetaway
from yoloify.pinboard.forms import BoundsForm


# Simplier task for a single update.
@shared_task
def update_cached_instance(instance):
    instance.update()


# Simple wrapper to control access to cached objects. It only applies
# to user-specific objects, so both 'requesting_user_id' and
# 'target_user_id' properties are set.
def allow_if_owner(method):
    def method_wrapper(self, *args, **kwargs):
        logger = logging.getLogger(__name__)
        if not hasattr(self, 'target_user_id') or not hasattr(self, 'requesting_user_id'):
            logger.warning('insufficient data for access control')
            return None
        if self.target_user_id == self.requesting_user_id:
            return method(self, *args, **kwargs)
        logger.warning('target_user_id (%s) != requesting_user_id (%s)' % (
            self.target_user_id,
            self.requesting_user_id,
        ))
        return None
    return method_wrapper


# Base class representing cached instances.
# It is purely an interface to the caching and the background task
# systems. It's ok to have several instances of this class for one
# actual cached instance.
class CachedInstance(object):

    def __init__(self, *args, **kwargs):
        for key in kwargs:
            value = kwargs[key]
            try:
                value = int(value)
            except ValueError:
                pass
            setattr(self, key, value)

    def background_update(self):
        update_cached_instance.apply_async(
            (self,),
            task_id=self.get_task_id(),
            queue='cache-queue'
        )

    def update(self):
        pass

    def get_task_id(self):
        pass


# The base class for cached pinboards objects.
class CachedPinboard(CachedInstance):

    def __init__(self, pinboard_name, *args, **kwargs):
        super(CachedPinboard, self).__init__(*args, **kwargs)
        self.name = pinboard_name

    def get_task_id(self):
        return self.name

    def get_part_cache_key(self, part_number):
        return "cached_pinboard:%s:part:%d" % (self.name, part_number)

    def get_part(self, part_number):
        cache = get_cache('default')
        key = self.get_part_cache_key(part_number)
        pins = cache.get(key)
        if pins is None:
            self.update()
            pins = cache.get(key)
        return pins

    def update(self):
        cache = get_cache('default')
        begin = 0
        end = settings.PINBOARD_PART_SIZE
        part_number = 0
        pins = list(self.get_queryset())
        pinboard_part = pins[begin:end]
        while pinboard_part:
            cache.set(
                self.get_part_cache_key(part_number),
                pinboard_part,
            )
            begin += settings.PINBOARD_PART_SIZE
            end += settings.PINBOARD_PART_SIZE
            part_number += 1
            pinboard_part = pins[begin:end]
        # the part sequence is somewhat NULL-terminated
        cache.delete(self.get_part_cache_key(part_number))

    # This method should be redefined in subclasses.
    def get_queryset(self):
        pass

    # Auxiliary method for getting Django queryset objects for the pins
    # created within a year that are the original pins for their goals.
    # The query also performs prefetching of related objects required
    # to render the pinboard htmls.
    @staticmethod
    def get_original_pins_for_goals():
        pins = Pin.objects\
            .filter(user=F('goal__user'))\
            .prefetch_related('user')\
            .prefetch_related('goal')
        return pins


class GoalsCachedPinboard(CachedPinboard):

    def __init__(self, *args, **kwargs):
        super(GoalsCachedPinboard, self).__init__('goals', *args, **kwargs)

    def get_queryset(self):
        return CachedPinboard.get_original_pins_for_goals().order_by("-goal__pin_count")\


class RecentCachedPinboard(CachedPinboard):

    def __init__(self, *args, **kwargs):
        super(RecentCachedPinboard, self).__init__('recent', *args, **kwargs)

    def get_queryset(self):
        return CachedPinboard.get_original_pins_for_goals().order_by("-created_at")


class CompletedCachedPinboard(CachedPinboard):

    def __init__(self, *args, **kwargs):
        super(CompletedCachedPinboard, self).__init__('completed', *args, **kwargs)

    def get_queryset(self):
        return CachedPinboard.get_original_pins_for_goals().order_by("-goal__complete_count").exclude(goal__complete_count=0)


class FriendsCachedPinboard(CachedPinboard):

    def __init__(self, *args, **kwargs):
        self.user_id = int(kwargs['target_user_id'])
        pinboard_name = 'friends_%d' % self.user_id
        super(FriendsCachedPinboard, self).__init__(pinboard_name, *args, **kwargs)

    def get_queryset(self):
        try:
            user = User.objects.get(id=self.user_id)
        except User.DoesNotExist:  # User gone
            return Pin.objects.none()

        profile = user.get_profile()
        following = [up.user.id for up in profile.following.all().prefetch_related('user')]
        pins = Pin.objects\
            .filter(user=F('goal__user'), bookmarked=True)\
            .filter(user__in=following)\
            .order_by("-goal__pin_count")\
            .prefetch_related('user')\
            .prefetch_related('goal')
        return pins


class ProfileGoalsCachedPinboard(CachedPinboard):

    def __init__(self, *args, **kwargs):
        self.user_id = int(kwargs['target_user_id'])
        pinboard_name = 'profile_goals_%d' % self.user_id
        super(ProfileGoalsCachedPinboard, self).__init__(pinboard_name, *args, **kwargs)

    def get_queryset(self):
        pins = Pin.objects.filter(user=self.user_id, bookmarked=True)\
            .prefetch_related('user')\
            .prefetch_related('goal')
        return pins


class ProfileCompletedCachedPinboard(CachedPinboard):

    def __init__(self, *args, **kwargs):
        self.user_id = int(kwargs['target_user_id'])
        pinboard_name = 'profile_completed_%d' % self.user_id
        super(ProfileCompletedCachedPinboard, self).__init__(pinboard_name, *args, **kwargs)

    def get_queryset(self):
        pins = Pin.objects.filter(user=self.user_id, complete=True)\
            .prefetch_related('user')\
            .prefetch_related('goal')
        return pins


class LocalPinboard(CachedPinboard):

    def __init__(self, *args, **kwargs):
        super(LocalPinboard, self).__init__('local', *args, **kwargs)

    def get_part(self, part_number):
        begin = part_number * settings.PINBOARD_PART_SIZE
        end = (part_number + 1) * settings.PINBOARD_PART_SIZE

        lng = getattr(self, 'lng', None)
        lat = getattr(self, 'lat', None)
        within = getattr(self, 'within', None)

        if lng and lat and within:
            qs = CachedPinboard.get_original_pins_for_goals()
            my_location = fromstr('POINT(%s %s)' % (lng, lat))
            locations = Location.objects.filter(point__distance_lte=(my_location, D(mi=within)))
            qs = qs.filter(goal__location__in=locations)
            category = getattr(self, 'category', None)
            if category:
                qs = qs.filter(goal__category=category)
            if getattr(self, 'among', None) == 'friends':
                me = User.objects.get(id=self.requesting_user_id)
                qs = qs.filter(user__profile__in=me.profile.following.all())
            return qs\
                .prefetch_related('user')\
                .prefetch_related('goal')\
                .order_by("-goal__pin_count")[begin:end]
        else:
            return Pin.objects.none()


class MapPinboard(CachedPinboard):

    def __init__(self, *args, **kwargs):
        super(MapPinboard, self).__init__('map', *args, **kwargs)

    def get_part(self, part_number):
        begin = part_number * settings.PINBOARD_PART_SIZE
        end = (part_number + 1) * settings.PINBOARD_PART_SIZE

        form = BoundsForm({
            'top': getattr(self, 'top', None),
            'bottom': getattr(self, 'bottom', None),
            'left': getattr(self, 'left', None),
            'right': getattr(self, 'right', None)
        })
        if not form.is_valid():
            return Pin.objects.none()

        locations_qs = Location.objects.filter(point__within=form.get_polygon())
        qs = CachedPinboard.get_original_pins_for_goals().filter(goal__location__in=locations_qs).distinct()
        category = getattr(self, 'category', None)
        if category:
            qs = qs.filter(goal__category=category)
        if getattr(self, 'among', None) == 'friends':
            me = User.objects.get(id=self.requesting_user_id)
            qs = qs.filter(user__profile__in=me.profile.following.all())
        return qs\
            .prefetch_related('user')\
            .prefetch_related('goal')\
            .order_by("-goal__pin_count")[begin:end]



class CityCategoryPinboard(CachedPinboard):
    def __init__(self, *args, **kwargs):
        self.city_id = int(kwargs['city_id'])
        self.category_id = int(kwargs['category_id'])
        pinboard_name = 'city_%d_category_%s' % (self.city_id, self.category_id)
        super(CityCategoryPinboard, self).__init__(pinboard_name, *args, **kwargs)

    def get_part(self, part_number):
        begin = part_number * settings.PINBOARD_PART_SIZE
        end = (part_number + 1) * settings.PINBOARD_PART_SIZE
        city = City.objects.get(id=self.city_id)
        my_location = fromstr('POINT(%s %s)' % city.location.point.coords)
        locations = Location.objects.filter(point__distance_lte=(my_location, D(mi=city.radius)))
        qs = CachedPinboard.get_original_pins_for_goals().filter(goal__location__in=locations, goal__category__id=self.category_id).distinct()

        return qs.prefetch_related('user').prefetch_related('goal').order_by("-goal__pin_count")[begin:end]
        
class CityGetawayPinboard(CachedPinboard):
    def __init__(self, *args, **kwargs):
        self.city_id = int(kwargs['city_id'])
        self.getaway_id = int(kwargs['getaway_id'])
        pinboard_name = 'city_%d_getaway_%s' % (self.city_id, self.getaway_id)
        super(CityGetawayPinboard, self).__init__(pinboard_name, *args, **kwargs)

    def get_part(self, part_number):
        begin = part_number * settings.PINBOARD_PART_SIZE
        end = (part_number + 1) * settings.PINBOARD_PART_SIZE
        getaway = CityGetaway.objects.get(id=self.getaway_id)
        my_location = fromstr('POINT(%s %s)' % getaway.location.point.coords)
        locations = Location.objects.filter(point__distance_lte=(my_location, D(mi=getaway.radius)))
        qs = CachedPinboard.get_original_pins_for_goals().filter(goal__location__in=locations).distinct()

        return qs.prefetch_related('user').prefetch_related('goal').order_by("-goal__pin_count")[begin:end]

class SearchPinboard(CachedPinboard):

    def __init__(self, *args, **kwargs):
        super(SearchPinboard, self).__init__('search', *args, **kwargs)

    def get_part(self, part_number):
        if self.query:
            begin = part_number * settings.PINBOARD_PART_SIZE
            end = (part_number + 1) * settings.PINBOARD_PART_SIZE

            sqs = SearchQuerySet().filter(content=self.query).order_by("-pin_count").load_all()
            page = sqs[begin:end]
            return map(lambda sr: sr.object, filter(lambda sr: sr, page))
        else:
            return Pin.objects.none()



CACHED_PINBOARD_CLASSES_BY_NAME = {
    'goals': GoalsCachedPinboard,
    'recent': RecentCachedPinboard,
    'completed': CompletedCachedPinboard,
    'friends': FriendsCachedPinboard,
    'profile_goals': ProfileGoalsCachedPinboard,
    'profile_completed': ProfileCompletedCachedPinboard,
    'local': LocalPinboard,
    'map': MapPinboard,
    'city_category': CityCategoryPinboard,
    'city_getaway': CityGetawayPinboard,
    'search': SearchPinboard
}


def get_cached_pinboard(pinboard_name, *args, **kwargs):
    pinboard_class = CACHED_PINBOARD_CLASSES_BY_NAME.get(pinboard_name)
    if pinboard_class:
        return pinboard_class(*args, **kwargs)
    return None


class UserSpecificCache(CachedInstance):

    VARIABLE = 'yoloify.pinboard.tasks.UserSpecificCache.variable'
    LOCK = '%s.lock' % VARIABLE

    @staticmethod
    def get_likes_cache_key(user_id):
        return "cached_pinboard:likes:%s" % user_id

    @staticmethod
    def get_likes(user_id):
        cache = get_cache('default')
        key = UserSpecificCache.get_likes_cache_key(user_id)
        likes = cache.get(key)
        if not likes:
            UserSpecificCache.update_likes(user_id)
            likes = cache.get(key)
        return likes

    @staticmethod
    def get_repins_cache_key(user_id):
        return "cached_pinboard:repins:%s" % user_id

    @staticmethod
    def get_repins(user_id):
        cache = get_cache('default')
        key = UserSpecificCache.get_repins_cache_key(user_id)
        repins = cache.get(key)
        if not repins:
            UserSpecificCache.update_repins(user_id)
            repins = cache.get(key)

        return repins

    @staticmethod
    def query_likes(user_id):
        goals = Pin.objects.filter(user=user_id, liked=True).prefetch_related('goal').values('goal')
        return [goal['goal'] for goal in goals]

    @staticmethod
    def query_repins(user_id):
        goals = Pin.objects.filter(user=user_id, bookmarked=True).prefetch_related('goal').values('goal')
        return [goal['goal'] for goal in goals]

    @staticmethod
    def update_likes(user_id):
        cache = get_cache('default')
        cache.set(
            UserSpecificCache.get_likes_cache_key(user_id),
            UserSpecificCache.query_likes(user_id),
        )

    @staticmethod
    def update_repins(user_id):
        cache = get_cache('default')
        cache.set(
            UserSpecificCache.get_repins_cache_key(user_id),
            UserSpecificCache.query_repins(user_id),
        )

    @staticmethod
    def get_current_users_ids():
        lock = Redis().lock(UserSpecificCache.LOCK)
        lock.acquire()
        Redis().setnx(UserSpecificCache.VARIABLE, json.dumps([]))
        current_users_ids = Redis().get(UserSpecificCache.VARIABLE)
        lock.release()
        current_users_ids = json.loads(current_users_ids)
        return current_users_ids

    @staticmethod
    def add_current_user_id(user_id):
        lock = Redis().lock(UserSpecificCache.LOCK)
        lock.acquire()
        Redis().setnx(UserSpecificCache.VARIABLE, json.dumps([]))
        current_users_ids = Redis().get(UserSpecificCache.VARIABLE)
        current_users_ids = json.loads(current_users_ids)
        if user_id not in current_users_ids:
            current_users_ids.append(user_id)
            Redis().set(UserSpecificCache.VARIABLE, json.dumps(current_users_ids))
        lock.release()

    def get_task_id(self):
        return 'user_specific_cache'

    def update(self):

        current_users_ids = UserSpecificCache.get_current_users_ids()
        for user_id in current_users_ids:
            friends_pinboard = FriendsCachedPinboard(target_user_id=user_id)
            friends_pinboard.update()
            profile_goals_pinboard = ProfileGoalsCachedPinboard(target_user_id=user_id)
            profile_goals_pinboard.update()
            profile_completed_pinboard = ProfileCompletedCachedPinboard(target_user_id=user_id)
            profile_completed_pinboard.update()

            UserSpecificCache.update_likes(user_id)
            UserSpecificCache.update_repins(user_id)


# Start periodic cache updates.
@shared_task
def periodic_cache_updates():
    for name in ['goals', 'recent', 'completed']:
        get_cached_pinboard(name).background_update()


@shared_task
def update_index():
    from haystack.management.commands.update_index import Command
    Command().handle(age=24,remove=True)


def cache_update(sender, *args, **kwargs):
    pin = kwargs['instance']
    get_cached_pinboard('goals').background_update()
    get_cached_pinboard('recent').background_update()
    get_cached_pinboard('completed').background_update()
    get_cached_pinboard('profile_goals', target_user_id=pin.user_id).background_update()
    get_cached_pinboard('profile_completed', target_user_id=pin.user_id).background_update()
    for follower in pin.user.profile.followers.all():
        get_cached_pinboard('friends', target_user_id=follower.user_id).background_update()

post_save.connect(cache_update, sender=Goal)


@shared_task
def update_pin_like_bookmark_count():
    bookmarks_count = Pin.objects.filter(bookmarked=True).values('goal').annotate(total=Count('id'))
    completes_count = Pin.objects.filter(complete=True).values('goal').annotate(total=Count('id'))

    for bookmark in bookmarks_count:
        goal = Goal.objects.select_for_update().get(pk=bookmark['goal'])
        goal.pin_count = bookmark['total']
        goal.save()

    for c in completes_count:
        goal = Goal.objects.select_for_update().get(pk=c['goal'])
        goal.complete_count = c['total']
        goal.save()


@shared_task
def ping_google():
    from django.contrib.sitemaps import ping_google
    ping_google()
