# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Pin.liked'
        db.add_column(u'pinboard_pin', 'liked',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Pin.bookmarked'
        db.add_column(u'pinboard_pin', 'bookmarked',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Pin.complete'
        db.add_column(u'pinboard_pin', 'complete',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Pin.created_at'
        db.add_column(u'pinboard_pin', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2014, 12, 20, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'Pin.updated_at'
        db.add_column(u'pinboard_pin', 'updated_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.datetime(2014, 12, 20, 0, 0), blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Pin.liked'
        db.delete_column(u'pinboard_pin', 'liked')

        # Deleting field 'Pin.bookmarked'
        db.delete_column(u'pinboard_pin', 'bookmarked')

        # Deleting field 'Pin.complete'
        db.delete_column(u'pinboard_pin', 'complete')

        # Deleting field 'Pin.created_at'
        db.delete_column(u'pinboard_pin', 'created_at')

        # Deleting field 'Pin.updated_at'
        db.delete_column(u'pinboard_pin', 'updated_at')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'pinboard.goal': {
            'Meta': {'object_name': 'Goal'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['pinboard.LocationCategory']", 'null': 'True', 'on_delete': 'models.DO_NOTHING', 'blank': 'True'}),
            'complete_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dominant_color': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'hike_detail': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '5000', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'image_author': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'image_source': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'like_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'goals'", 'null': 'True', 'to': u"orm['pinboard.Location']"}),
            'pin_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'pin_type': ('django.db.models.fields.CharField', [], {'default': "'location'", 'max_length': '10'}),
            'site_url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'tags': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'goals'", 'to': u"orm['auth.User']"})
        },
        u'pinboard.like': {
            'Meta': {'object_name': 'Like'},
            'end_valid': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'goal': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'likes'", 'to': u"orm['pinboard.Goal']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start_valid': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'likes'", 'to': u"orm['auth.User']"})
        },
        u'pinboard.location': {
            'Meta': {'object_name': 'Location'},
            'address': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'bounds': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'place': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'})
        },
        u'pinboard.locationcategory': {
            'Meta': {'ordering': "['name']", 'object_name': 'LocationCategory'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_hike': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'pinboard.pin': {
            'Meta': {'unique_together': "(('goal', 'user', 'end_valid'),)", 'object_name': 'Pin'},
            'bookmarked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'completed': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_valid': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'goal': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pins'", 'to': u"orm['pinboard.Goal']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'liked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_valid': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pins'", 'to': u"orm['auth.User']"})
        },
        u'pinboard.temporaryimage': {
            'Meta': {'object_name': 'TemporaryImage'},
            'created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['pinboard']