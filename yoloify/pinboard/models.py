from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db.models import PointField, GeoManager
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Count
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.contrib import comments
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from django.utils.timezone import make_naive
from django.utils import timezone
from django.template.defaultfilters import slugify
from feedly.activity import Activity

from sorl.thumbnail import get_thumbnail
from PIL import Image
import pytz

from yoloify.pinboard import verbs as PinVerb
from yoloify.pinboard.pin_feedly import feedly
from yoloify.utils.views import break_down_phone_number

PINTYPES = (
    ('goal', 'Goal'),
    ('location', 'Location')
)
PIN_ACTIONS = (
    ('1', 'Make Reservation'),
    ('2', 'Book Online'),
    ('3', 'Reserve your Spot'),
    ('4', 'View Class Schedule'),
    ('5', 'View Events Calendar')
)


class LocationCategory(models.Model):
    name = models.CharField(_('name'), max_length=200)
    is_hike = models.BooleanField(default=True)
    created = models.DateTimeField(_('creation date'), auto_now_add=True)

    def __unicode__(self):
        return u'{0}'.format(self.name)

    class Meta:
        ordering = ["name"]


class Location(models.Model):
    address = models.CharField(max_length=200, blank=False, default='')
    neighborhood = models.CharField(max_length=200, blank=True, null=True)
    bounds = models.CharField(max_length=200, blank=False, default='')
    point = PointField(null=True)
    place = models.CharField(max_length=200, blank=False, default='')  # TODO remove
    created = models.DateTimeField(_('creation date'), auto_now_add=True)

    objects = GeoManager()


class Goal(models.Model):
    user = models.ForeignKey(User, related_name='goals')
    title = models.CharField(_('title'), max_length=200)
    tag_line = models.CharField(_('tag_line'), max_length=300, blank=True)
    features = models.TextField(_('features'), blank=True)
    description = models.TextField(_('description'), blank=True)
    tags = models.TextField(_('tags'), blank=True)
    phone_number = models.CharField(_('phone number'), max_length=100, blank=True)
    image = models.ImageField(_('image'), upload_to='goals')
    image_author = models.CharField(_('author'), max_length=200, blank=True)
    image_source = models.URLField(_('source'), blank=True)
    ###### Field for location type ##########
    pin_type = models.CharField(max_length=10, default='location', choices=PINTYPES)
    site_url = models.CharField(max_length=1000, default='', blank=True)
    category = models.ForeignKey(LocationCategory, blank=True, null=True, on_delete=models.DO_NOTHING)
    hike_detail = models.CharField(max_length=5000, default='', blank=True)
    location = models.ForeignKey(Location, blank=True, null=True, related_name='goals')
    #########################################
    dominant_color = models.CharField(max_length=6, editable=False)
    pin_count = models.IntegerField(default=0, editable=False)
    complete_count = models.IntegerField(default=0, editable=False)
    like_count = models.IntegerField(default=0, editable=False)
    created = models.DateTimeField(_('creation date'), auto_now_add=True)
    action_button_text = models.CharField(max_length=2, blank=True, null=True, choices=PIN_ACTIONS)
    action_button_link = models.CharField(max_length=250, blank=True, null=True)
    deal_button_link = models.CharField(max_length=250, blank=True, null=True)
    deal_active = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s' % self.title

    def merge_to(self, to):
        to.pin_count += self.pin_count
        to.complete_count += self.complete_count
        self.pins.all().update(goal=to)
        self.pins.filter(liked=True).update(goal=to)

        for user_id in to.pins.values_list('user', flat=True).annotate(count=Count('id')).filter(count__gt=1):
            pins = to.pins.filter(user_id=user_id).order_by('-updated_at')
            first = pins[0]
            excess = pins.exclude(id=first.id)
            to.pin_count -= excess.count()
            to.complete_count -= excess.exclude(complete=False).count()
            excess.delete()

        to.save()

        ctype = ContentType.objects.get_for_model(self)
        qs = comments.get_model().objects.filter(
            content_type=ctype,
            object_pk=self.id,
            site__pk=settings.SITE_ID,
            is_public=True
        )
        qs.update(object_pk=to.pk)
        self.delete()

    def get_absolute_url(self):
        return reverse('pin', kwargs={'pk': self.pk})

    def is_reposted_by(self, user):
        return self.pins.filter(user=user, bookmarked=True).exists() and self.user != user

    def calculate_dominant_color(self):
        im = Image.open(self.image)
        color = im.convert('RGB').resize((1, 1), Image.ANTIALIAS).getpixel((0, 0))
        return "".join(map(lambda x: "%02X" % x, color[:3]))

    def save(self, *args, **kwargs):
        self.dominant_color = self.calculate_dominant_color()
        super(Goal, self).save(*args, **kwargs)

    def generate_normal_image(self):
        if not self.image:
            return None
        thumb = get_thumbnail(self.image, settings.PIN_SIZE, format="JPEG")
        return thumb

    @property
    def normal_image_url(self):
        thumb = self.generate_normal_image()
        if thumb:
            return thumb.url
        return None

    def generate_thumbnail(self):
        if not self.image:
            return None
        thumb = get_thumbnail(self.image, settings.PIN_THUMB_SIZE, crop="center", format="JPEG")
        return thumb

    @property
    def thumb_url(self):
        thumb = self.generate_thumbnail()
        if thumb:
            return thumb.url
        return None

    @property
    def comment_count(self):
        ctype = ContentType.objects.get_for_model(self)
        qs = comments.get_model().objects.filter(
            content_type=ctype,
            object_pk=self.id,
            site__pk=settings.SITE_ID,
            is_public=True
        )
        return qs.count()
    
    @property
    def formatted_phone(self):
        number = break_down_phone_number(self.phone_number)
        if number:
            return u"(%s) %s-%s" % number
        
    @property
    def operating_hours(self):
        from collections import defaultdict
        hours = defaultdict(list)
        for hour in self.hours.all().order_by('-from_hour'):
            hours[hour.get_weekday_display()].append({
                'open': hour.from_hour.strftime("%-I:%M%p").lower(),
                'close': hour.to_hour.strftime("%-I:%M%p").lower()
            })
        return hours


def pin_my_goal(sender, *args, **kwargs):
    goal = kwargs['instance']
    created = kwargs['created']
    if created:
        pin = Pin(goal=goal, user=goal.user, bookmarked=True)
        pin.bookmarked_at = timezone.now()
        pin.save()
        feedly.add_pin(pin, pin.user.id, PinVerb.Create)

post_save.connect(pin_my_goal, sender=Goal)


class Pin(models.Model):
    goal = models.ForeignKey(Goal, related_name='pins')
    user = models.ForeignKey(User, related_name='pins')
    liked = models.BooleanField(default=False)
    liked_at = models.DateTimeField(blank=True, null=True)
    bookmarked = models.BooleanField(default=False)
    bookmarked_at = models.DateTimeField(blank=True, null=True)
    complete = models.BooleanField(default=False)
    complete_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super(Pin, self).__init__(*args, **kwargs)
        self._old_completed = self.complete
        self._old_bookmarked = self.bookmarked
        self._old_liked = self.liked

    @property
    def is_repin(self):
        return self.user != self.goal.user

    def is_reposted_by(self, user):
        return self.goal.is_reposted_by(user)

    @property
    def slug_title(self):
        return slugify(self.goal.title)

    class Meta:
        # The reason to have the three fields unique together is actually
        # to have a single valid pin for the same goal and user, so the
        # desired constraint would be something like:
        #   unique_together('goal', 'user') if end_valid is None
        # Because it's practically impossible to have two pins with
        # same goals, users, and end_valid times that aren't None,
        # this constraint works fine.
        unique_together = ('goal', 'user')

    def create_activity(self, actor_id, verb):
        activity = Activity(
            actor=actor_id,
            verb=verb,
            object=self.id,  # The id of the newly created Pin object
            target=self.goal_id,
            time=make_naive(self.created_at, pytz.utc)
        )
        return activity


def pin_post_save(sender, *args, **kwargs):
    pin = kwargs['instance']
    created = kwargs['created']
    goal = Goal.objects.select_for_update().get(pk=pin.goal_id)
    if created:
        if pin.bookmarked:
            goal.pin_count += 1
            goal.save()

post_save.connect(pin_post_save, sender=Pin)



class TemporaryImage(models.Model):
    image = models.ImageField(_('image'), upload_to="temp_images")
    created = models.DateField(_('creation date'), auto_now_add=True)


class MetaInfo(models.Model):
    """
    Common model for meta data
    """
    meta_title = models.CharField(
        max_length=68,
        blank=True,
        null=True,
        help_text='This is the page title, that appears in the title bar (68 chars).'
    )
    meta_description = models.TextField(
        blank=True,
        null=True,
        help_text='A short description, displayed in search results.'
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Comma-separated keywords for search engines (255 chars).'
    )
    meta_heading = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='This is the page heading (255 chars).'
    )
    og_image = models.ImageField(_('image'), upload_to='meta')

    class Meta:
        abstract = True


class City(MetaInfo):
    """
    City Model
    """
    name = models.CharField(max_length=50)
    categories = models.ManyToManyField(LocationCategory, through='CityCategory')
    thumbnail = models.ImageField(_('image'), upload_to='cities')
    location = models.ForeignKey(Location, blank=True, null=True, related_name='cities')
    radius = models.PositiveSmallIntegerField(default=15, help_text='Query radius in miles')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='order')
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(_('creation date'), auto_now_add=True)

    class Meta:
        ordering = ['order']
        db_table = 'city'
        verbose_name_plural = 'cities'

    def __unicode__(self):
        return u'{0}'.format(self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('city', None, {'city_id': self.id, 'city_name': slugify(self.name)})

    def generate_thumbnail(self):
        if not self.thumbnail:
            return None
        thumb = get_thumbnail(self.thumbnail, settings.CITYPIC_SIZE, crop="center", format="JPEG")
        return thumb

    @property
    def thumb_url(self):
        thumb = self.generate_thumbnail()
        if thumb:
            return thumb.url
        return None
        
    @property
    def slug_city_name(self):
        return slugify(self.name)    


class CityCategory(MetaInfo):
    """
    City Category
    """
    city = models.ForeignKey(City)
    category = models.ForeignKey(LocationCategory)
    thumbnail = models.ImageField(_('image'), upload_to='categories')
    order = models.PositiveSmallIntegerField(verbose_name='order')
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(_('creation date'), auto_now_add=True)

    class Meta:
        ordering = ["order"]
        db_table = 'city_category'
        verbose_name_plural = 'city_categories'

    def __unicode__(self):
        return u'{0}:{1}'.format(self.city.name, self.category.name)

    @models.permalink
    def get_absolute_url(self):
        return ('city_category', None, {'city_cat_id': self.id,'cat_name': slugify(self.category.name),'city_name': slugify(self.city.name)})

    def generate_thumbnail(self):
        if not self.thumbnail:
            return None
        thumb = get_thumbnail(self.thumbnail, settings.CATEGORYPIC_SIZE, crop="center", format="JPEG")
        return thumb

    @property
    def thumb_url(self):
        thumb = self.generate_thumbnail()
        if thumb:
            return thumb.url
        return None
        
    @property
    def slug_city_name(self):
        return slugify(self.city)     
        
    @property
    def slug_citycat_name(self):
        return slugify(self.category) 

class CityGetawayList(MetaInfo):
    """
    City Category List
    """
    name = models.CharField(max_length=50)
    city = models.ForeignKey(City)
    thumbnail = models.ImageField(_('image'), upload_to='getawaylist')
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(_('creation date'), auto_now_add=True)

    class Meta:
        db_table = 'city_getawaylist'
        verbose_name_plural = 'city_getawaylists'

    def __unicode__(self):
        return u'{0}:{1}'.format(self.city.name, self.id)

    @models.permalink
    def get_absolute_url(self):
        return ('city_getawaylist', None, {'city_getawaylist_id': self.id, 'city_name': slugify(self.city.name)})
        
    def generate_thumbnail(self):
        if not self.thumbnail:
            return None
        thumb = get_thumbnail(self.thumbnail, settings.CATEGORYPIC_SIZE, crop="center", format="JPEG")
        return thumb

    @property
    def thumb_url(self):
        thumb = self.generate_thumbnail()
        if thumb:
            return thumb.url
        return None
        
    @property
    def slug_city_name(self):
        return slugify(self.city)     
        



class CityGetaway(MetaInfo):
    """
    City Weekend Getaway
    """
    name = models.CharField(max_length=50)
    city = models.ForeignKey(CityGetawayList, related_name="getaway_city")
    citygetawaylist = models.ForeignKey(CityGetawayList, related_name="getaway_list")
    thumbnail = models.ImageField(_('image'), upload_to='getaways')
    order = models.PositiveSmallIntegerField(verbose_name='order')
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(_('creation date'), auto_now_add=True)
    location = models.ForeignKey(Location, blank=True, null=True, related_name='city_getaway')
    radius = models.PositiveSmallIntegerField(default=15, help_text='Query radius in miles')
    tag_line = models.CharField(_('tag_line'), max_length=300, blank=True)
    features = models.TextField(_('features'), blank=True)
    description = models.TextField(_('description'), blank=True)
    
    class Meta:
        ordering = ["order"]
        db_table = 'city_getaway'
        verbose_name_plural = 'city_getaways'

    def __unicode__(self):
        return u'{0}:{1}'.format(self.city.name, self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('city_getaway', None, {'city_getaway_id': self.id,'getaway_name': slugify(self.name),'city_name': slugify(self.city.name)})
        

    def generate_thumbnail(self):
        if not self.thumbnail:
            return None
        thumb = get_thumbnail(self.thumbnail, settings.CATEGORYPIC_SIZE, crop="center", format="JPEG")
        return thumb

    @property
    def thumb_url(self):
        thumb = self.generate_thumbnail()
        if thumb:
            return thumb.url
        return None
        
    @property
    def slug_getaway_city(self):
        return slugify(self.city.name)     
        
    @property
    def slug_getaway_name(self):
        return slugify(self.name)     
        


#To load the verbs
from yoloify.pinboard import verbs
