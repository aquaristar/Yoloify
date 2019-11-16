# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StaticPage'
        db.create_table(u'pages_staticpage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('content', self.gf('tinymce.models.HTMLField')()),
        ))
        db.send_create_signal(u'pages', ['StaticPage'])


    def backwards(self, orm):
        # Deleting model 'StaticPage'
        db.delete_table(u'pages_staticpage')


    models = {
        u'pages.staticpage': {
            'Meta': {'object_name': 'StaticPage'},
            'content': ('tinymce.models.HTMLField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['pages']