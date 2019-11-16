from django.db import models
from tinymce.models import HTMLField


class StaticPage(models.Model):
    title = models.CharField(max_length=128)
    description = models.CharField(max_length=256, blank=True, null=True)
    slug = models.CharField(max_length=32)
    content = HTMLField()