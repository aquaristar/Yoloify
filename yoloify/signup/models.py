import datetime
import random
from hashlib import sha1, md5
from django.core import validators
from django.db import models
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import utc
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.core.cache import get_cache
from django.utils.http import urlquote
from django.utils.encoding import force_bytes
import re
from sorl.thumbnail import get_thumbnail
from yoloify.utils.djangoshortcuts import build_template_cache_key
from django.core.mail import EmailMessage

class Profile(models.Model):
    username = models.CharField(_('username'), max_length=30, unique=True, blank=True, null=True, default=None,
        validators=[validators.RegexValidator(re.compile('^[\w0-9_]{4,30}$'),
                                              _('Required. 4 to 30 characters. Letters, numbers and _ character'),
                                              'invalid')])
    user = models.OneToOneField(User, related_name='profile')
    userpic = models.ImageField(_('user picture'), upload_to='userpics', null=True, blank=True)
    about = models.TextField(_('about'), null=True, blank=True)
    followers = models.ManyToManyField('self', related_name='following', blank=True, symmetrical=False)
    location = models.CharField(_('location'), max_length=64, null=True, blank=True)
    is_signup_finished = models.BooleanField(_('active'), default=False)
    last_activity = models.DateTimeField(_('Last Activity'), null=True, blank=True)

    def __unicode__(self):
        return self.user.email

    def userpic_url(self):
        if not self.userpic:
            return None
        thumb = get_thumbnail(self.userpic, settings.USERPIC_SIZE, crop="center", format="JPEG")
        return thumb.url

    def generate_userpic_large(self):
        if not self.userpic:
            return None
        pic = get_thumbnail(self.userpic, settings.USERPIC_LARGE_SIZE, crop="center", format="JPEG")
        return pic

    def userpic_large_url(self):
        pic = self.generate_userpic_large()
        if not pic:
            return None
        return pic.url

    def userpic_small_url(self):
        if not self.userpic:
            return None
        thumb = get_thumbnail(self.userpic, settings.USERPIC_SMALL_SIZE, crop="center", format="JPEG")
        return thumb.url

    @property
    def is_email_confirmed(self):
        return not hasattr(self.user, 'email_confirmation')


class EmailConfirmation(models.Model):

    user = models.OneToOneField(User, related_name='email_confirmation', editable=False)
    key = models.CharField(_('confirmation key'), max_length=40, editable=False)
    last_sent = models.DateTimeField(_('last time confirmation was sent'), null=True)

    def __unicode__(self):
        return self.key

    def save(self, *args, **kwargs):
        if not self.key:
            salt = sha1(str(random.random())).hexdigest()[:5]
            self.key = sha1(salt+self.user.username).hexdigest()
        super(EmailConfirmation, self).save(*args, **kwargs)

    def send(self, update_timestamp=True):
        site = Site.objects.get_current()
        context = {
            'confirmation': self,
            'site_name': site.name,
            'first_name': self.user.first_name,
            'confirmation_url': 'http://%s%s' % (site.domain, reverse('confirm_email', kwargs={
                'username': self.user.username,
                'key': self.key
                }))
            }
        #subject = render_to_string('signup/email_confirmation_subject.txt', context)
        #message = render_to_string('signup/email_confirmation_message.txt', context)


        #Mandrill template
        msg = EmailMessage(to=[self.user.email])
        # A Mandrill template name
        msg.template_name = "emailconfirmation"           
        
        # Content blocks to fill in

        # Merge tags in your template
        msg.global_merge_vars = {                       
            'CONFIRMATION_URL': 'http://%s%s' % (site.domain, reverse('confirm_email', kwargs={
                'username': self.user.username,
                'key': self.key
                }))
        }
        # Per-recipient merge tags
        msg.merge_vars = {                              
            self.user.email: {'NAME': self.user.first_name},
        }
        msg.use_template_subject = True
        msg.use_template_from = True
        msg.send()


       # email = send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email])
        if update_timestamp:
            self.last_sent = datetime.datetime.utcnow().replace(tzinfo = utc)
            self.save()
        return msg

    def confirm(self, key):
        if self.key == key:
            self.delete()
            return True
        return False


class PasswordReset(models.Model):
    user = models.ForeignKey(User, related_name='password_resets', editable=False)
    key = models.CharField(_('confirmation key'), max_length=40, editable=False)
    last_sent = models.DateTimeField(_('last time reset instruction were sent'), null=True)

    def __unicode__(self):
        return self.key

    def save(self, *args, **kwargs):
        if not self.key:
            salt = sha1(str(random.random())).hexdigest()[:5]
            self.key = sha1(salt+self.user.username).hexdigest()
        super(PasswordReset, self).save(*args, **kwargs)

    def send(self, update_timestamp=True, use_https=False):
        site = Site.objects.get_current()
        protocol = 'https' if use_https else 'http'
        context = {
            'reset': self,
            'username': self.user.username,
            'site_name': site.name,
            'reset_url': '%s://%s%s' % (protocol, site.domain, reverse('reset_password_confirm', kwargs={
                'username': self.user.username,
                'key': self.key
            }))
        }
     #   subject = render_to_string('signup/password_reset_subject.txt', context)
     #   message = render_to_string('signup/password_reset_message.txt', context)


        #Mandrill template
        msg = EmailMessage(to=[self.user.email])
        # A Mandrill template name
        msg.template_name = "password-reset"           
        
        # Content blocks to fill in

        # Merge tags in your template
        msg.global_merge_vars = {                       
            'RESET_URL': '%s://%s%s' % (protocol, site.domain, reverse('reset_password_confirm', kwargs={
                'username': self.user.username,
                'key': self.key
            }))
        }
        # Per-recipient merge tags
        msg.merge_vars = {                              
            self.user.email: {'NAME': self.user.first_name},
        }
        msg.use_template_subject = True
        msg.use_template_from = True
        msg.send()


        #email = send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email])
        if update_timestamp:
            self.last_sent = datetime.datetime.utcnow().replace(tzinfo = utc)
            self.save()
        return msg

    def verify(self, key):
        return self.key == key

def drop_profile_cache(sender, *args, **kwargs):
    profile = kwargs['instance']
    cache = get_cache('default')
    key = build_template_cache_key('profile-data', profile.user.username)
    cache.delete(key)
    key = build_template_cache_key('profile-pic', profile.user.username)
    cache.delete(key)
post_save.connect(drop_profile_cache, sender=Profile)
