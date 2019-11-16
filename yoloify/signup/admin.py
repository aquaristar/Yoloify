from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin, StackedInline
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.shortcuts import render
from yoloify.signup.models import Profile


class ProfileInline(StackedInline):
    model = Profile

    def has_delete_permission(self, request, obj=None):
        return False


class MyUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    actions = ['export']

    def export(self, request):
        response = render(request, 'admin/auth/user/export.csv', {'users': User.objects.all()}, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users.csv"'
        return response

    def get_urls(self):
        from django.conf.urls import patterns
        return patterns('',
            (r'^export/$', self.export)
        ) + super(MyUserAdmin, self).get_urls()


admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)