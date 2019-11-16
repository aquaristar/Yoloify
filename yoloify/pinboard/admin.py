import json
from django import forms
from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.messages import success
from django.db import transaction
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from yoloify.pinboard.models import Goal, LocationCategory, Location, City, CityCategory, CityGetaway, CityGetawayList
from yoloify.utils.views import break_down_phone_number
from yoloify.opening_hours.admin import OpeningHoursInline

class LocationWidget(forms.Widget):

    def value_from_datadict(self, data, files, name):
        location = json.loads(data.get(name+'_location'))
        point = 'POINT(%s %s)' % (location['lng'], location['lat'])
        bounds = data.get(name+'_bounds')
        neighborhood = data.get(name+'_neighborhood')
        qs = Location.objects.filter(
            bounds=bounds,
            point=point,
            neighborhood=neighborhood
        )
        if qs.exists():
            return qs[0]
        location = Location()
        location.point = point
        location.address = data.get(name+'_helper')
        location.bounds = bounds
        location.neighborhood = neighborhood
        location.save()
        return location

    def render(self, name, value, attrs=None):
        if isinstance(value, int):
            value = Location.objects.get(id=value)
        bounds = json.loads(value.bounds) if value and value.bounds else None

        kwargs = {
            'name': name
        }
        if value:
            kwargs.update({
                'lat': value.point[1],
                'lng': value.point[0],
                'address': value.address,
                'neighborhood': value.neighborhood
            })
        if bounds:
            kwargs.update({
                'sw_lat': bounds['sw']['lat'],
                'sw_lng': bounds['sw']['lng'],
                'ne_lat': bounds['ne']['lat'],
                'ne_lng': bounds['ne']['lng']
            })
        return render_to_string('admin/pinboard/goal/location_widget.html', kwargs)

    class Media:
        js = (
            '//maps.googleapis.com/maps/api/js?v=3.exp&libraries=places',
            'js/vendor/jquery.js', 'js/vendor/underscore.js'
        )


class HikeDetailWidget(forms.Widget):

    def render(self, name, value, attrs=None):
        return render_to_string('admin/pinboard/goal/hike_detail_widget.html', {
            'name': name,
            'detail': json.loads(value) if value else None,
            'value': value
        })

    class Media:
        js = ['js/vendor/jquery.js']


class PreviewFileInput(forms.ClearableFileInput):

    def render(self, name, value, attrs=None):
        site = Site.objects.get_current()
        url = ( 'http://%s%s' % (site.domain, value.url) ) if value and hasattr(value, 'url') else ''
        return mark_safe(super(PreviewFileInput, self).render(name, value, attrs) + """
<br /><br /><img src="%(url)s" class="%(name)s_preview" style="max-width: 500px;" />
<script>
$(function() {
    var $input = $('[name=%(name)s]');
    var $img = $('img.%(name)s_preview');
    $input.change(function() {
        var files = $input.get(0).files;
        if (files) {
            var reader = new FileReader();
            reader.onload = function (e) {
                $img.attr('src', e.target.result);
            }
            reader.readAsDataURL(files[0]);
        } else {
            $img.attr('src', null);
        }
    });

});
</script>
        """ % {
            'name': name,
            'url': url,
        })

    class Media:
        js = ['js/vendor/jquery.js']


class PhoneWidget(forms.Widget):

    def render(self, name, value, attrs=None):
        print value
        detail = break_down_phone_number(value)
        return render_to_string('admin/pinboard/goal/phone_widget.html', {
            'name': name,
            'detail': detail,
            'value': value
        })

    class Media:
        js = ['js/vendor/jquery.js']


class GoalForm(forms.ModelForm):
    location = forms.Field(widget=LocationWidget, required=False)
    hike_detail = forms.Field(widget=HikeDetailWidget, required=False)
    phone_number = forms.Field(widget=PhoneWidget, required=False)

    image = forms.ImageField(widget=PreviewFileInput)

    class Meta:
        model = Goal
        fields = ['user', 'title', 'features', 'tag_line', 'description', 'tags', 'phone_number', 'image', 'image_author', 'image_source', 'pin_type', 'site_url', 'category', 'location', 'hike_detail', 'action_button_text', 'action_button_link', 'deal_button_link', 'deal_active']

    def clean_hike_detail(self):
        hike_detail = self.cleaned_data.get('hike_detail')
        if hike_detail:
            payload = json.loads(hike_detail)
            for part in ('trail', 'elevation', 'highest'):
                val = payload[part]['amount']
                if val:
                    try:
                        float(val)
                    except ValueError:
                        raise forms.ValidationError(_('All values must be specified as numbers.'))
        return hike_detail

    def clean(self):
        if self.cleaned_data['category'] and self.cleaned_data['category'].is_hike:
            detail = self.cleaned_data.get('hike_detail')
            if detail:
                detail = json.loads(detail)
            if not detail or (not detail['trail']['amount'] and not detail['elevation']['amount'] and not detail['highest']['amount']):
                raise forms.ValidationError(_('Hike detail must be specified'))
        return self.cleaned_data


class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created', 'deal_active')
    search_fields = ['title']
    list_filter = ('category', 'deal_active')
    inlines = [OpeningHoursInline, ]
    
    form = GoalForm

    def search(self, request):
        try:
            goal = Goal.objects.get(id=request.REQUEST.get('to'))
            site = Site.objects.get_current()
            return HttpResponse(json.dumps({
                'to': goal.pk,
                'title': goal.title,
                'thumb_url': "http://%s%s" % (site.domain, goal.thumb_url)
            }))
        except Exception:
            return HttpResponseNotFound()

    @transaction.commit_on_success
    def merge(self, request):

        try:
            goal = Goal.objects.get(id=request.REQUEST.get('goal'))
            to = Goal.objects.get(id=request.REQUEST.get('to'))
            success(request, mark_safe(_('<strong>%s</strong> successfully merged to <strong>%s</strong>.') % (goal.title, to.title)))
            goal.merge_to(to)
            return HttpResponseRedirect('../../goal/%s/' % to.pk)
        except Exception:
            return HttpResponseNotFound()

    def get_urls(self):
        from django.conf.urls import patterns
        return patterns('',
            (r'^search/$', self.search),
            (r'^merge/$', self.merge),
        ) + super(GoalAdmin, self).get_urls()

admin.site.register(Goal, GoalAdmin)


class LocationCategoryAdmin(admin.ModelAdmin):

    list_display = ('name', 'is_hike')

admin.site.register(LocationCategory, LocationCategoryAdmin)


class CityForm(forms.ModelForm):
    location = forms.Field(widget=LocationWidget, required=False)
    thumbnail = forms.ImageField(widget=PreviewFileInput)
    og_image = forms.ImageField(widget=PreviewFileInput, required=False)

    class Meta:
        model = City
        fields = ['name', 'order', 'visible', 'radius', 'thumbnail', 'location', 'meta_title', 'meta_description', 'meta_keywords','og_image', 'meta_heading']


class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'order', 'radius', 'visible', 'created_at')
    list_filter = ('visible', )
    search_fields = ['name']
    form = CityForm

admin.site.register(City, CityAdmin)


class CityCategoryForm(forms.ModelForm):
    thumbnail = forms.ImageField(widget=PreviewFileInput)
    og_image = forms.ImageField(widget=PreviewFileInput, required=False)

    class Meta:
        model = CityCategory
        fields = ['city', 'category', 'order', 'visible', 'thumbnail', 'meta_title', 'meta_description', 'meta_keywords','og_image', 'meta_heading']


class CityCategoryAdmin(admin.ModelAdmin):
    list_display = ('city', 'category', 'order', 'visible', 'created_at')
    list_filter = ('city', 'category', 'visible')
    search_fields = ['city__name', 'category__name']
    form = CityCategoryForm

admin.site.register(CityCategory, CityCategoryAdmin)

class CityGetawayForm(forms.ModelForm):
    location = forms.Field(widget=LocationWidget, required=False)
    thumbnail = forms.ImageField(widget=PreviewFileInput)
    og_image = forms.ImageField(widget=PreviewFileInput, required=False)

    class Meta:
        model = CityGetaway
        fields = ['city', 'citygetawaylist', 'name', 'order', 'visible', 'radius', 'thumbnail', 'location', 'meta_title', 'meta_description', 'meta_keywords','og_image', 'meta_heading']

class CityGetawayAdmin(admin.ModelAdmin):
    list_display = ('city', 'order', 'visible', 'created_at')
    list_filter = ('city', 'visible')
    search_fields = ['city__name', 'name']
    form = CityGetawayForm

admin.site.register(CityGetaway, CityGetawayAdmin)

class CityGetawayListForm(forms.ModelForm):
    thumbnail = forms.ImageField(widget=PreviewFileInput)
    og_image = forms.ImageField(widget=PreviewFileInput, required=False)

    class Meta:
        model = CityGetawayList
        fields = ['city', 'name', 'visible', 'thumbnail', 'meta_title', 'meta_description', 'meta_keywords','og_image', 'meta_heading']


class CityGetawayListAdmin(admin.ModelAdmin):
    list_display = ('city', 'visible', 'created_at')
    list_filter = ('city', 'visible')
    search_fields = ['city__name']
    form = CityGetawayListForm

admin.site.register(CityGetawayList, CityGetawayListAdmin)