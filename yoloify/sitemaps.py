from datetime import datetime, timedelta
from django.contrib import sitemaps
from django.core.urlresolvers import reverse
from django.db.models import F, Max
from yoloify.pinboard.models import Pin, City, CityCategory, CityGetawayList, CityGetaway
from yoloify.signup.models import Profile

class PagesSitemap(sitemaps.Sitemap):
    def items(self):
        return ['home', 'login', 'signup', 'map', 'local']

    def location(self, page):
        return reverse(page)


class PinSitemap(sitemaps.Sitemap):
    def items(self):
        return Pin.objects\
              .filter(user=F('goal__user'))\
            

    def location(self, pin):
        return '/pin/%s/%s/' % (pin.id, pin.slug_title)

    changefreq = 'always'

    def lastmod(self, obj):
        return obj.updated_at
        
 #City        
class CitySitemap(sitemaps.Sitemap):
    def items(self):
        return City.objects\
              .all()\
            

    def location(self, city):
        return '/local/%s/things-to-do-in-%s/' % (city.id, city.slug_city_name)

    changefreq = 'always'

#City Category
class CityCategorySitemap(sitemaps.Sitemap):
    def items(self):
        return CityCategory.objects\
              .all()\
            

    def location(self, city):
        return '/local/%s/%s-near-%s/' % (city.id, city.slug_citycat_name, city.slug_city_name)

    changefreq = 'always'
  
  
#City Getaway list
  
class CityGetawayListSitemap(sitemaps.Sitemap):
    def items(self):
        return CityGetawayList.objects\
              .all()\

    def location(self, getawaylist):
        return '/local/%s/weekend-getaways-from-%s/' % (getawaylist.id, getawaylist.slug_city_name)

    changefreq = 'always'

#City Getaways
  
class CityGetawaySitemap(sitemaps.Sitemap):
    def items(self):
        return CityGetaway.objects\
              .all()\

    def location(self, getaways):
        return '/local/%s/getaway-from-%s-to-%s/' % (getaways.id, getaways.slug_getaway_city, getaways.slug_getaway_name, )

    changefreq = 'always'

class ProfileSitemap(sitemaps.Sitemap):
    def items(self):
        return Profile.objects\
            .filter(is_signup_finished=True)\
            .filter(user__is_active=True)

    def location(self, profile):
        return '/profile/%s/' % profile.id

    changefreq = 'always'

    def lastmod(self, obj):
        return obj.last_activity