from feedly.feeds.redis import RedisFeed


class PinFeed(RedisFeed):
    key_format = 'feed:normal:%(user_id)s'


class UserPinFeed(PinFeed):
    key_format = 'feed:user:%(user_id)s'
