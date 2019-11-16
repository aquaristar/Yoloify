import json
from django.contrib.auth import get_user
from rest_framework import serializers
from rest_framework.fields import ImageField, Field
from yoloify.pinboard.models import Pin, Goal
from django.utils.dateformat import format
from django.core.urlresolvers import reverse


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ('id', 'title', 'description', 'image')


class PinSerializer(serializers.ModelSerializer):
    title = Field(source='goal.title')
    description = Field(source='goal.description')
    tags = Field(source='goal.tags')
    tag_line = Field(source='goal.tag_line')
    features = Field(source='goal.features')
    operating_hours = Field(source='goal.operating_hours')
    phone_number = Field('goal.formatted_phone')
    slug_title = Field(source='slug_title')
    author = Field(source='goal.user.get_full_name')
    author_id = Field(source='goal.user.profile.id')
    author_image = Field(source='goal.user.profile.userpic_url')

    user = Field(source='user_id')
    image = ImageField(source='goal.image', read_only=True)
    image_url = Field(source='goal.normal_image_url')
    thumb_url = Field(source='goal.thumb_url')
    image_source = Field(source='goal.image_source')
    image_author = Field(source='goal.image_author')

    is_reposted = serializers.SerializerMethodField('get_is_reposted')
    is_owner = serializers.SerializerMethodField('get_is_owner')
    is_goal_owner = serializers.SerializerMethodField('get_is_goal_owner')
    is_repin = Field(source='is_repin')
    goal_created = serializers.SerializerMethodField('get_goal_created')

    like_count = Field(source='goal.like_count')
    complete_count = Field(source='goal.complete_count')
    pin_count = Field(source='goal.pin_count')
    comment_count = Field(source='goal.comment_count')

    type = Field(source='goal.pin_type')
    site_url = Field(source='goal.site_url')
    category_id = Field(source='goal.category.pk')
    category_name = Field(source='goal.category.name')
    category_is_hike = Field(source='goal.category.is_hike')
    hike_detail = Field(source='goal.hike_detail')
    l_address = Field(source='goal.location.address')
    l_neighborhood = Field(source='goal.location.neighborhood')
    l_bounds = Field(source='goal.location.bounds')
    l_place = serializers.SerializerMethodField('get_place')
    is_liked_by_me = serializers.SerializerMethodField('get_is_liked_by_me')
    is_completed_by_me = serializers.SerializerMethodField('get_is_completed_by_me')
    is_bookmarked_by_me = serializers.SerializerMethodField('get_is_bookmarked_by_me')
    action_button_text = serializers.SerializerMethodField('get_action_button_text')
    action_button_link = Field(source='goal.action_button_link')
    deal_button_link = Field(source='goal.deal_button_link')
    deal_active = Field(source='goal.deal_active')

    
    def get_place(self, pin):
        point = pin.goal.location.point
        return '{"lat":%s, "lng": %s}' % (point[1], point[0])

    def get_goal_created(self, pin):
        return int(format(pin.goal.created, "U"))*1000

    def get_is_reposted(self, pin):
        user = get_user(self.context['request'])
        if user.is_authenticated() and pin is not None:
            return pin.is_reposted_by(user)
        return False

    def get_is_owner(self, pin):
        user = get_user(self.context['request'])
        if pin is not None and pin.user == user:
            return True
        else:
            return False

    def get_is_goal_owner(self, pin):
        user = get_user(self.context['request'])
        if pin is not None and pin.goal.user == user:
            return True
        return False

    def get_is_liked_by_me(self, pin):
        user = get_user(self.context['request'])
        return user.is_authenticated() and Pin.objects.filter(goal=pin.goal, user=user, liked=True).exists()

    def get_is_completed_by_me(self, pin):
        user = get_user(self.context['request'])
        return user.is_authenticated() and Pin.objects.filter(goal=pin.goal, user=user, complete=True).exists()

    def get_is_bookmarked_by_me(self, pin):
        user = get_user(self.context['request'])
        return user.is_authenticated() and Pin.objects.filter(goal=pin.goal, user=user, bookmarked=True).exists()
    
    def get_action_button_text(self, pin):
        return pin.goal.get_action_button_text_display()
    
    class Meta:
        model = Pin
        fields = ('id', 'goal', 'author', 'author_id', 'author_image', 'user', 'title', 'tag_line', 'features', 'description', 'tags',
                  'operating_hours', 'phone_number', 'slug_title', 'slug_title', 'image', 'image_url', 'thumb_url',
                  'image_source', 'image_author', 'is_reposted', 'is_owner', 'is_goal_owner', 'is_repin',
                  'goal_created', 'like_count', 'complete_count', 'pin_count', 'comment_count', 'is_liked_by_me',
                  'type', 'site_url', 'category_id', 'category_name', 'category_is_hike', 'hike_detail',
                  'l_address', 'l_bounds', 'l_place', 'is_completed_by_me', 'is_bookmarked_by_me', 'action_button_text', 'action_button_link', 'deal_button_link', 'deal_active', 'l_neighborhood')
