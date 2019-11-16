# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'UsageStatsDaily.total_active_users'
        db.add_column(u'stats_usagestatsdaily', 'total_active_users',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'UsageStatsDaily.total_active_users'
        db.delete_column(u'stats_usagestatsdaily', 'total_active_users')


    models = {
        u'stats.usagestatsdaily': {
            'Meta': {'ordering': "('usage_date',)", 'object_name': 'UsageStatsDaily'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'total_active_users': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_comments': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_goal_completed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_goal_pin': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_goal_repin': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_likes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_location_completed': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_location_pin': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_location_repin': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'total_new_users': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'usage_date': ('django.db.models.fields.DateField', [], {})
        }
    }

    complete_apps = ['stats']