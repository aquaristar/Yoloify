# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UsageStatsDaily'
        db.create_table(u'stats_usagestatsdaily', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('usage_date', self.gf('django.db.models.fields.DateField')()),
            ('total_goal_pin', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('total_location_pin', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('total_goal_repin', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('total_location_repin', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('total_goal_completed', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('total_location_completed', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('total_likes', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('total_comments', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('total_new_users', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal(u'stats', ['UsageStatsDaily'])


    def backwards(self, orm):
        # Deleting model 'UsageStatsDaily'
        db.delete_table(u'stats_usagestatsdaily')


    models = {
        u'stats.usagestatsdaily': {
            'Meta': {'ordering': "('usage_date',)", 'object_name': 'UsageStatsDaily'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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