from django.conf import settings

import json
from redis import Redis

from yoloify.pinboard.tasks import UserSpecificCache

class CurrentUsersMiddleware(object):

    def process_request(self, request):
        if request.user.is_authenticated():
            UserSpecificCache.add_current_user_id(request.user.id)
