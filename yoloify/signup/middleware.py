from django.utils import timezone
from django.core.cache import get_cache
from yoloify.signup.models import Profile


class LastActivityMiddleware(object):

    @staticmethod
    def get_cache_key(user_id):
        return 'user_last_activity_time:%d' % user_id

    @staticmethod
    def get_last_activity_time(user_id):
        cache = get_cache('default')
        key = LastActivityMiddleware.get_cache_key(user_id)
        return cache.get(key)

    @staticmethod
    def get_inactivity_period_sec(user_id):
        last_time = LastActivityMiddleware.get_last_activity_time(user_id)
        if not last_time:
            return None
        return (timezone.now() - last_time).total_seconds()

    def process_request(self, request):
        if request.user.is_authenticated():
            cache = get_cache('default')
            key = LastActivityMiddleware.get_cache_key(request.user.id)
            now = timezone.now()
            cache.set(key, now)
            Profile.objects.filter(
                user__id=request.user.id
            ).update(last_activity=timezone.now())
