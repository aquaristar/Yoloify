from django.contrib import admin
from yoloify.opening_hours.models import OpeningHours


class OpeningHoursInline(admin.TabularInline):
    model = OpeningHours


class OpeningHoursAdmin(admin.ModelAdmin):
    list_display = ('goal', 'weekday', 'from_hour', 'to_hour')
    list_filter = ('weekday', )
    search_fields = ('goal__title', )

admin.site.register(OpeningHours, OpeningHoursAdmin)
