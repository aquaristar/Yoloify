from django.contrib import admin
from yoloify.pages.models import StaticPage


class StaticPageAdmin(admin.ModelAdmin):
    list_display = ('slug',)

admin.site.register(StaticPage, StaticPageAdmin)