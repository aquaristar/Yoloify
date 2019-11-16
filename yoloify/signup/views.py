import requests
import json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.contrib import auth, messages
from django.contrib.auth import get_user
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.cache import cache
from social.apps.django_app.default.models import UserSocialAuth
from yoloify.signup.forms import SignupForm, ConfirmationResendForm, PasswordResetForm, SetPasswordForm, SettingsForm, PasswordChangeForm
from yoloify.signup.models import EmailConfirmation, PasswordReset, Profile
from yoloify.utils.djangoshortcuts import build_template_cache_key
from yoloify.utils.views import send_signup_admin_notification


@csrf_protect
@never_cache
@transaction.commit_on_success
def signup(request):
    """Displays the registration form and handles the registration action."""

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email_confirmation.send(update_timestamp=False)
            messages.info(request, _('Confirmation email sent. Please check your mailbox.'))
            if getattr(settings, 'ADMIN_SIGNUP_NOTIFICATION', False):
                send_signup_admin_notification(user)
            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            auth.login(request, user)
            full_url = '/local/?ref=signup'
            return redirect(full_url)
    else:
        form = SignupForm()

    return render(request, 'signup/signup.html', {
        'form': form
    })


@csrf_protect
@never_cache
@transaction.commit_on_success
def confirmation_resend(request):
    initial = {}
    user = get_user(request)
    if user.is_authenticated():
        initial = {'email': user.email}
    if request.method == 'POST':
        form = ConfirmationResendForm(request.POST, initial=initial)
        if form.is_valid():
            form.save()
            return redirect('signup_done')
    else:
        form = ConfirmationResendForm(initial=initial)
    return render(request, 'signup/confirmation_resend.html', {
        'form': form
    })


@never_cache
@transaction.commit_on_success
def confirm_email(request, username, key):
    try:
        user = User.objects.get(username=username)
        confirmation = user.email_confirmation
    except (User.DoesNotExist, EmailConfirmation.DoesNotExist):
        user = None

    if user is not None and confirmation.confirm(key):
        # user.is_active = True
        # user.save()
        user.backend = settings.AUTHENTICATION_BACKENDS[0]
        auth.login(request, user)
        return redirect('settings')
    else:
        return render(request, 'signup/confirmation_invalid.html')


@never_cache
@transaction.commit_on_success
def reset_password(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('reset_password_sent')
    else:
        form = PasswordResetForm()

    return render(request, 'signup/password_reset.html', {
        'form': form
    })


@never_cache
@transaction.commit_on_success
def reset_password_confirm(request, username, key):
    try:
        user = User.objects.get(username=username)
        reset = user.password_resets.get(key=key)
    except (User.DoesNotExist, PasswordReset.DoesNotExist):
        user = None

    if user is not None:
        validlink = True
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                reset.delete()
                return redirect('reset_password_done')
            print form.errors
        else:
            form = SetPasswordForm(None)
    else:
        validlink = False
        form = None

    return render(request, 'signup/password_reset_confirm.html', {
        'validlink': validlink,
        'form': form
    })


@never_cache
def account_settings(request):
    user = get_user(request)

    form = None
    data = {}
    files = {}
    try:
        profile = user.get_profile()
        data.update({
            'username': profile.username,
            'about': profile.about,
            'location': profile.location
        })
        files.update({
            'userpic': profile.userpic,
        })
    except Profile.DoesNotExist:
        pass
    data.update({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    })

    if request.method == 'POST':
        data.update(request.POST.dict())
        files.update(request.FILES.dict())
        form = SettingsForm(instance = user, data = data, files = files)
        if form.is_valid():
            form.save()
            cache.delete(build_template_cache_key('profile-info', user.username))
            messages.info(request, _('Settings updated.'))
            return redirect('settings')
        else:
            messages.error(request, _('Please, correct the errors below.'))
    else:
        form = SettingsForm(instance = user, data = data, files = files)

    return render(request, 'signup/settings.html', {
        'form': form,
        'password_change_form': PasswordChangeForm(get_user(request)),
        'has_password': user.password != '!'
    })


@login_required
def friends(request):
    #Controlling frontend from backend is a bad idea,
    #here tab is selected from following code.
    me = get_user(request).get_profile()
    friends = []
    facebook_friends = []
    facebook_friends_here = []
    q = request.GET.get('search')
    following = Profile.objects.filter(
        followers=me
    ).prefetch_related('user')
    has_facebook_account = False

    section = 'following'
    if request.GET.get('followers') is not None:
        section = 'followers'
    if request.GET.get('facebook') is not None:
        section = 'facebook'
    if q is not None:
        section = 'search'

    if section == 'following':
        friends = following
    elif section == 'followers':
        friends = me.followers.all().prefetch_related('user')
    elif section == 'facebook':
        try:
            social_user = request.user.social_auth.get(provider='facebook')
            facebook_friends = fetch_facebook_friends(social_user)
            #Get all facebook users in Yoloify
            facebook_users = UserSocialAuth.objects.filter(
                provider='facebook'
            ).exclude(user=request.user).values_list('uid', flat=True)
            #Get all followings who are registered through facebook
            followings = UserSocialAuth.objects.filter(
                provider='facebook',
                user__profile__followers=me,
            ).exclude(user=request.user).values_list('uid', flat=True)
            #Get the profiles of facebook friends
            facebook_friends_here = UserSocialAuth.objects.filter(
                uid__in=facebook_friends_here
            ).values_list('user', flat=True)
            if facebook_friends_here:
                facebook_friends_here = Profile.objects.filter(
                    user__id__in=facebook_friends_here
                )
                if following:
                    following_ids = ','.join(map(lambda x: str(x), following.values_list('id', flat=True)))
                    facebook_friends_here = facebook_friends_here.extra(select={
                        'following_order': 'id in (%s)' % following_ids
                    }).order_by('following_order')
            else:
                facebook_friends_here = Profile.objects.none()
            has_facebook_account = True
        except UserSocialAuth.DoesNotExist:
            pass
    else:
        if q:
            friends = Profile.objects.exclude(id=me.id)
            friends = filter_by_name_or_email(friends, q)
            friends = friends.prefetch_related('user')
        else:
            friends = []

    return render(request, 'signup/friends.html', {
        'section': section,
        'friends': friends,
        'has_facebook_account': has_facebook_account,
        'facebook_friends': facebook_friends_here,
        'following': [f.pk for f in following],
        'q': q,
    })


def fetch_facebook_friends(social_user):
    cache_key = 'facebook_friends_%s' % social_user.uid
    facebook_friends = cache.get(cache_key)
    if not facebook_friends:
        url = u'https://graph.facebook.com/{0}/' \
              u'friends?fields=id,name' \
              u'&access_token={1}'.format(
                  social_user.uid,
                  social_user.extra_data['access_token'],
              )
        response = requests.get(url)
        #Fetch all facebook friends
        facebook_friends = response.json()['data']
        cache.set(cache_key, facebook_friends, 3600)

    return facebook_friends


def follow_facebook_friends(user):
    social_user = user.social_auth.get(provider='facebook')
    me = user.get_profile()
    facebook_friends = fetch_facebook_friends(social_user)
    facebook_friends_uid = [friend['id'] for friend in facebook_friends]
    facebook_friends_here = UserSocialAuth.objects.filter(
        provider='facebook',
        uid__in=facebook_friends_uid
    ).exclude(user=user).prefetch_related('user')
    for social_user in facebook_friends_here:
        profile = social_user.user.get_profile()
        profile.followers.add(me)
    


def filter_by_name_or_email(query, name):
    for term in name.split():
        query = query.filter(Q(user__first_name__icontains=term) | Q(user__last_name__icontains=term) | Q(about__icontains=term) | Q(user__email__iexact=term))
    return query


@login_required
def check_social_user(request, provider, user_id):
    found = False
    try:
        UserSocialAuth.objects.get(provider=provider, uid=user_id)
        found = True
    except UserSocialAuth.DoesNotExist:
        pass

    return HttpResponse(
        json.dumps({'found': found}),
        mimetype="application/json",
        status=200,
    )
