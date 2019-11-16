import json
import math
from crispy_forms.layout import Submit
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import fromstr
from django.core.urlresolvers import reverse
from django.core.cache import get_cache
from django.conf import settings
from django.db.models import F
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import ugettext as _
from django.utils.http import urlencode
from crispy_forms.helper import FormHelper
from django.views.generic import CreateView, View
from yoloify.pinboard.models import Pin, Location, LocationCategory, City, CityCategory, CityGetaway, CityGetawayList
from yoloify.pinboard.forms import NewGoalForm, NewLocationGoalForm
from yoloify.signup.models import Profile
from yoloify.utils.views import LoginRequiredMixin, json_date_handler
from yoloify.utils.djangoshortcuts import build_template_cache_key
from yoloify.pinboard.tasks import get_cached_pinboard, UserSpecificCache
from yoloify.pinboard.pin_feedly import feedly
from yoloify.pinboard.forms import BoundsForm
from yoloify.pinboard.tasks import CachedPinboard


class CreateNewPinView(LoginRequiredMixin, View):

    def get(self, request):
        return redirect('home')

    def post(self, request):
        pinForm = NewLocationGoalForm(request.POST, request.FILES)
        if not pinForm.is_valid():
            return redirect('profile')

        locationModel = Location(
            address=request.POST.get('address'),
            neighborhood=request.POST.get('neighborhood'),
            bounds=request.POST.get('bounds'),
            place=request.POST.get('place')
        )
        coord = json.loads(request.POST.get('place'))
        locationModel.point = ( 'POINT(%s %s)' % (coord['lng'], coord['lat']) )
        locationModel.save()

        newPinModel = pinForm.save(commit=False)
        newPinModel.location = locationModel
        newPinModel.user = get_user(request)
        newPinModel.save()

        UserSpecificCache.update_repins(pinForm.instance.user.id)
        get_cached_pinboard(
            'profile_goals',
            target_user_id=pinForm.instance.user.id,
        ).update()
        return redirect('profile')


class CreatePinView(LoginRequiredMixin, CreateView):
    model = Pin
    form_class = NewGoalForm
    template_name = 'pinboard/create.html'

    def get(self, request):
        return redirect('home')

    def get_form_class(self):
        form_class = super(CreatePinView, self).get_form_class()
        form_class.helper = FormHelper()
        form_class.helper.add_input(Submit('submit', _('Create')))
        return form_class

    def form_valid(self, form):
        form.instance.user = get_user(self.request) # pre-set author
        result = super(CreatePinView, self).form_valid(form)

        UserSpecificCache.update_repins(form.instance.user.id)
        get_cached_pinboard(
            'profile_goals',
            target_user_id=form.instance.user.id,
        ).update()

        return result

    def get_success_url(self):
        return reverse('profile')


def pin(request, pk, slug):
    pin = get_object_or_404(Pin, pk=pk)
    return render(request, 'pinboard/pin.html', {
        'pin': pin
    })


def profile(request, profile_id=None):
    user = get_user(request)
    me = user.get_profile() if user.is_authenticated() else None
    if profile_id is None:
        if me is None:
            return redirect('home')
        else:
            profile = me
            target_user_id = me.user.id
    else:
        profile = get_object_or_404(Profile, pk=profile_id)
        target_user_id = profile.user.id
    followers = profile.followers.all().prefetch_related('user')
    following = Profile.objects.filter(followers=profile).prefetch_related('user')
    is_following = me in profile.followers.all()

    section = 'goals'
    if request.GET.get('completed', None) is not None:
        section = 'completed'

    context = {
        'is_following': is_following,
        'followers': followers,
        'following': following,
        'profile': profile,
        'section': section,
        'likes': [],
        'pins': []
    }

    pinboard_name = 'profile_%s' % section
    pinboard = get_cached_pinboard(
        pinboard_name,
        requesting_user_id=0,
        target_user_id=target_user_id,
    )
    context['pinboard_name'] = pinboard_name
    context['part_parameters'] = urlencode({
        'part_number': 0,
        'target_user_id': target_user_id,
    })

    context['more'] = bool(pinboard.get_part(0))

    return render(request, 'pinboard/profile.html', context)


@login_required
def follow(request, profile_id=None):
    profile = get_object_or_404(Profile, pk=profile_id)
    me = get_user(request).get_profile()
    if me != profile:
        profile.followers.add(me)
        cache = get_cache('default')
        key = build_template_cache_key('profile-followers', profile.user.username)
        cache.delete(key)
        key = build_template_cache_key('profile-followers', me.user.username)
        cache.delete(key)
    if request.is_ajax():
        return HttpResponse(
            json.dumps({'message': 'Success'}),
            mimetype="application/json",
            status=200,
        )
    else:
        return redirect('profile', profile.id)


@login_required
def unfollow(request, profile_id=None):
    profile = get_object_or_404(Profile, pk=profile_id)
    me = get_user(request).get_profile()
    if me != profile:
        profile.followers.remove(me)
        cache = get_cache('default')
        key = build_template_cache_key('profile-followers', profile.user.username)
        cache.delete(key)
        key = build_template_cache_key('profile-followers', me.user.username)
        cache.delete(key)

    if request.is_ajax():
        return HttpResponse(
            json.dumps({'message': 'Success'}),
            mimetype="application/json",
            status=200,
        )
    else:
        return redirect('profile', profile.id)

@login_required
def search(request):
    profile = get_user(request).get_profile()
    query = request.GET.get('query', '')

    pinboard_name = 'search'
    pinboard = get_cached_pinboard(
        pinboard_name,
        requesting_user_id=request.user.id,
        target_user_id=request.user.id,
        query=query
    )
    more = bool(pinboard.get_part(0))
    part_parameters = {
        'part_number': 0,
        'target_user_id': request.user.id,
    }
    return render(request, 'pinboard/search.html', {
        'profile': profile,
        'pins': [],
        'pinboard_name': pinboard_name,
        'part_parameters': urlencode(part_parameters),
        'more': more,
        'likes': [],
        'repins': [],
        'query': query
    })


@login_required
def trending(request):
    profile = get_user(request).get_profile()

    section = 'all'
    pinboard_name = 'goals'
    if request.GET.get('recent') is not None:
        section = 'recent'
        pinboard_name = 'recent'
    elif request.GET.get('completed') is not None:
        section = 'completed'
        pinboard_name = 'completed'
    elif request.GET.get('friends') is not None:
        section = 'friends'
        pinboard_name = 'friends'

    pinboard = get_cached_pinboard(
        pinboard_name,
        requesting_user_id=request.user.id,
        target_user_id=request.user.id,
    )
    more = bool(pinboard.get_part(0))
    part_parameters = {
        'part_number': 0,
        'target_user_id': request.user.id,
    }

    return render(request, 'pinboard/trending.html', {
        'profile': profile,
        'section': section,
        'pins': [],
        'pinboard_name': pinboard_name,
        'part_parameters': urlencode(part_parameters),
        'more': more,
        'likes': [],
        'repins': [],
    })


def local(request):
    user = get_user(request)
    profile = user.get_profile() if user.is_authenticated() else None

    return render(request, 'pinboard/local.html', {
        'profile': profile,
        'cities': City.objects.filter(visible=True)
    })


def city(request, city_id, city_name):
    user = get_user(request)
    profile = user.get_profile() if user.is_authenticated() else None

    return render(request, 'pinboard/city.html', {
        'profile': profile,
        'city': City.objects.get(id=city_id),
        'city_categories': CityCategory.objects.filter(city_id=city_id, visible=True),
        'city_getawaylists': CityGetawayList.objects.filter(city_id=city_id, visible=True)
    })


def city_getawaylist(request, city_getawaylist_id, city_name):
    user = get_user(request)
    profile = user.get_profile() if user.is_authenticated() else None
    city_getawaylist = CityGetawayList.objects.get(id=city_getawaylist_id)


    return render(request, 'pinboard/city_getaways.html', {
        'profile': profile,
        'city': city_getawaylist.city,
        'city_getaways': CityGetaway.objects.filter(city=city_getawaylist, visible=True),
        'city_getawaylist': city_getawaylist,
        
    })


def city_category(request, city_cat_id, cat_name, city_name):
    user = get_user(request)
    profile = user.get_profile() if user.is_authenticated() else None
    city_cat = CityCategory.objects.get(id=city_cat_id)

    pinboard_name = 'city_category'
    pinboard = get_cached_pinboard(
        pinboard_name,
        city_id=city_cat.city.id,
        category_id=city_cat.category.id
    )
    more = bool(pinboard.get_part(0))
    part_parameters = {
        'part_number': 0,
        'city_id': city_cat.city.id,
        'category_id': city_cat.category.id
    }

    return render(request, 'pinboard/city_pins.html', {
        'profile': profile,
        'city': city_cat.city,
        'category': city_cat.category,
        'city_cat': city_cat,
        'pins': [],
        'pinboard_name': pinboard_name,
        'part_parameters': urlencode(part_parameters),
        'more': more,
        'likes': [],
        'repins': [],
    })


def city_getaway(request, city_getaway_id, getaway_name, city_name):
    user = get_user(request)
    profile = user.get_profile() if user.is_authenticated() else None
    city_getaway = CityGetaway.objects.get(id=city_getaway_id)

    pinboard_name = 'city_getaway'
    pinboard = get_cached_pinboard(
        pinboard_name,
        city_id=city_getaway.city.id,
        getaway_id=city_getaway.id
    )
    more = bool(pinboard.get_part(0))
    part_parameters = {
        'part_number': 0,
        'city_id': city_getaway.city.id,
        'getaway_id': city_getaway.id,
        

    }

    return render(request, 'pinboard/getaway_pins.html', {
        'profile': profile,
        'city': city_getaway.city,
        'city_getaway': city_getaway,
        'pins': [],
        'pinboard_name': pinboard_name,
        'part_parameters': urlencode(part_parameters),
        'more': more,
        'likes': [],
        'repins': [],
    })



def map(request):
    user = get_user(request)
    profile = get_user(request).get_profile() if user.is_authenticated() else None
    pinboard_name = 'map'

    more = True
    part_parameters = {
        'part_number': 0,
        'target_user_id': request.user.id if user.is_authenticated() else None,
    }

    return render(request, 'pinboard/map.html', {
        'profile': profile,
        'pins': [],
        'pinboard_name': pinboard_name,
        'part_parameters': urlencode(part_parameters),
        'more': more,
        'likes': [],
        'repins': [],
        'categories': LocationCategory.objects.all()
    })


def map_list(request):
    user = get_user(request)
    profile = user.get_profile() if user.is_authenticated() else None
    pinboard_name = 'local'

    pinboard = get_cached_pinboard(
        pinboard_name,
        requesting_user_id=user.id if user.is_authenticated() else 0,
        target_user_id=user.id if user.is_authenticated() else 0,
        )
    more = bool(pinboard.get_part(0))
    part_parameters = {
        'part_number': 0,
        'target_user_id': user.id if user.is_authenticated() else 0,
        }

    return render(request, 'pinboard/map_list.html', {
        'profile': profile,
        'pins': [],
        'pinboard_name': pinboard_name,
        'part_parameters': urlencode(part_parameters),
        'more': more,
        'likes': [],
        'repins': [],
        'categories': LocationCategory.objects.all()
    })


def next_part(request, pinboard_name):
    user = get_user(request)
    part_number = int(request.GET.get('part_number'))
    pinboard = get_cached_pinboard(
        pinboard_name,
        requesting_user_id=user.id if user.is_authenticated() else 0,
        **request.GET.dict()
    )
    pins = pinboard.get_part(part_number)
    likes = UserSpecificCache.get_likes(user.id) if user.is_authenticated() else []
    repins = UserSpecificCache.get_repins(user.id) if user.is_authenticated() else []
    more = bool(pinboard.get_part(part_number + 1))
    part_parameters = request.GET.dict()
    part_parameters.update({
        'part_number': part_number + 1,
    })

    return render(request, 'pinboard/_pinboard_part.html', {
        'pins': pins,
        'pinboard_name': pinboard_name,
        'part_number': part_number,
        'part_parameters': urlencode(part_parameters),
        'more': more,
        'likes': likes,
        'repins': repins,
    })

TILE_SIZE = 256 # Google Maps constant
ORIGIN = [TILE_SIZE/2, TILE_SIZE/2]
PIXELS_PER_LNG_DEG = TILE_SIZE / 360.;
PIXELS_PER_LNG_RAD = TILE_SIZE / (2*math.pi);
THRESHOLD = 36 # pixels

def latlng_to_point(latlng):
    x = ORIGIN[0] + latlng[1] * PIXELS_PER_LNG_DEG;
    siny = bound(math.sin(math.radians(latlng[0])), -0.9999, 0.9999)
    y = ORIGIN[1] + 0.5 * math.log((1+siny)/(1-siny)) * -PIXELS_PER_LNG_RAD;
    return x, y

def point_to_pixels(xy, zoom):
    tiles = 1 << zoom
    return xy[0]*tiles, xy[1]*tiles

def bound(value, min_value=None, max_value=None):
    if min_value: value = max(min_value, value)
    if max_value: value = min(max_value, value)
    return value

def map_markers(request):
    form = BoundsForm(request.REQUEST)
    if not form.is_valid():
        return HttpResponseBadRequest(form.errors)

    locations_qs = Location.objects.filter(point__within=form.get_polygon()).exclude(goals__isnull=True)
    qs = CachedPinboard.get_original_pins_for_goals().filter(goal__location__in=locations_qs).distinct()
    category = request.REQUEST.get('category')
    if category:
        qs = qs.filter(goal__category=category)
    if request.REQUEST.get('among') == 'friends':
        qs = qs.filter(user__profile__in=get_user(request).profile.following.all())

    pins = []
    for id, point_raw in qs.values_list('id', 'goal__location__point'):
        point = fromstr(point_raw)
        x, y = point_to_pixels(latlng_to_point((point[1], point[0])), form.cleaned_data['zoom'])
        pins.append( (id, x, y, point[0], point[1]) )

    pin_to_cluster = {}
    index = 0
    clusters = []
    while pins:
        id, x, y, lng, lat = pins.pop()
        left, right = x, x
        top, bottom = y, y
        left_deg, right_deg = lng, lng
        top_deg, bottom_deg = lat, lat
        cluster = [id]
        pin_to_cluster[id] = index

        pins_upd = []
        for id, x, y, lng, lat in pins:
            if  ( max(right, x) - min(left, x) <= THRESHOLD )\
            and ( max(bottom, y) - min(top, y) <= THRESHOLD ):
                cluster.append(id)
                pin_to_cluster[id] = index
                left_deg = min(left_deg, lng)
                right_deg = max(right_deg, lng)
                top_deg = min(top_deg, lat)
                bottom_deg = max(bottom_deg, lat)
            else:
                pins_upd.append( (id, x, y, lng, lat) )
        clusters.append({
            'center': {
                'lng': (left_deg+right_deg)/2.,
                'lat': (top_deg+bottom_deg)/2.
            },
            'ids': cluster,
            'bounds': {
                'sw': {
                    'lng': left_deg,
                    'lat': top_deg
                },
                'ne': {
                    'lng': right_deg,
                    'lat': bottom_deg
                }
            }
        })
        index += 1
        pins = pins_upd

    return HttpResponse(json.dumps({
        'clusters': clusters,
        'id_to_cluster': pin_to_cluster
    }), content_type='application/json')


def enrich_activities(activities):
    '''
    Load the models attached to these activities
    (Normally this would hit a caching layer like memcached or redis)
    '''
    result = []
    pin_ids = []
    actor_ids = []
    for a in activities:
        pin_ids.append(a.object_id)
        actor_ids.append(a.actor_id)

    profiles = Profile.objects.filter(user_id__in=actor_ids)

    pin_dict = Pin.objects.in_bulk(pin_ids)
    for a in activities:
        pin = pin_dict.get(a.object_id)
        if not pin:
            feedly.remove_pin(a.actor_id, a)
            continue
        try:
            a.actor = profiles.get(user_id=a.actor_id)
            a.pin = pin
            result.append(a)
        except Profile.DoesNotExist:
            pass

    return result


@login_required
def newsfeed(request, template_name='pinboard/newsfeed.html'):
    feeds = feedly.get_feeds(request.user.id)['normal']

    if not request.is_ajax():
        return render(request, template_name, {
            'feed_pins': [],
            'more': bool(len(feeds)),
            'next_page': 0
        })

    try:
        page = int(request.GET.get('page'))
    except (ValueError, TypeError):
        page = 0

    total_totals = len(feeds)
    begin = page * settings.PINBOARD_PART_SIZE
    end = begin + settings.PINBOARD_PART_SIZE
    next_page = page + 1

    if request.REQUEST.get('delete'):
        feeds.delete()
    activities = list(feeds[begin:end])
    if request.REQUEST.get('raise'):
        raise Exception(activities)

    more = True if total_totals > end else False
    activities = enrich_activities(activities)
    likes = UserSpecificCache.get_likes(request.user.id)
    repins = UserSpecificCache.get_repins(request.user.id)

    return render(request, 'pinboard/_feed_part.html', {
        'feed_pins': activities,
        'more': more,
        'next_page': next_page,
        'likes': likes,
        'repins': repins
    })


class LocalView(LoginRequiredMixin, View):
    template_name = 'pinboard/local.html'

    def get(self, request):
        user = get_user(request)
        me = user.get_profile() if user.is_authenticated() else None
        profile = me
        target_user_id = me.user.id if user.is_authenticated() else 0

        followers = profile.followers.all().prefetch_related('user')
        following = Profile.objects.filter(followers=profile).prefetch_related('user')
        is_following = me in profile.followers.all()

        section = 'goals'
        if request.GET.get('completed', None) is not None:
            section = 'completed'

        pinboard_name = 'profile_%s' % section

        pinboard = get_cached_pinboard(
            pinboard_name,
            requesting_user_id=user.id if user.is_authenticated() else 0,
            target_user_id=target_user_id,
        )
        more = bool(pinboard.get_part(0))
        part_parameters = {
            'part_number': 0,
            'target_user_id': target_user_id,
        }

        return render(request, self.template_name, {
            'is_following': is_following,
            'followers': followers,
            'following': following,
            'profile': profile,
            'section': section,
            'pins': [],
            'pinboard_name': pinboard_name,
            'part_parameters': urlencode(part_parameters),
            'more': more,
            'likes': [],
        })

    def post(self, request):
        return HttpResponse('')

def profile_by_username(request, username):
    lower = username.lower()
    if lower != username:
        return redirect('profile-by-username', username=lower)
    return profile(request, get_object_or_404(Profile, username=username).id)