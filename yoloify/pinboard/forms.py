from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.gis.geos import MultiPolygon
from yoloify.pinboard.models import Goal, TemporaryImage, LocationCategory
from django.utils.translation import ugettext_lazy as _
import urllib2
from django.core.files import File
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from tempfile import SpooledTemporaryFile
import urlparse
import os
import random
import string
import zlib
import gzip
import StringIO

from django.utils.html import escape


class FetchException(Exception):
    pass

# fetch image from given url and return Django File object
def fetch_image(url):
    # download the file and keep it into temporary file
    opener = urllib2.build_opener()
    opener.addheaders = [('Accept-encoding', 'gzip, deflate')]
    connection = opener.open(url)
    try:
        file_size = int(connection.info().getheaders('Content-Length')[0])
    except Exception:
        raise FetchException(_('Can\'t fetch the download file size.'))
    if file_size > settings.UPLOAD_FILE_MAX_SIZE:
        raise FetchException(
            _('The download file size is too big. The size should be less than %s.') %\
            filesizeformat(settings.UPLOAD_FILE_MAX_SIZE))

    data = connection.read()

    # check for encoding and decompress if needed
    encoding = connection.headers.get('Content-Encoding')
    if encoding == 'deflate':
        try:
            data = zlib.decompress(data)
        except zlib.error:
            data = zlib.decompress(data, -zlib.MAX_WBITS)
    elif encoding == 'gzip':
        compressed = StringIO.StringIO()
        compressed.write(data)
        compressed.seek(0)
        decompressed = gzip.GzipFile(fileobj=compressed, mode='rb')
        data = decompressed.read()

    img_temp = SpooledTemporaryFile(max_size=512)
    img_temp.write(data)
    img_temp.flush()

    # try to get file extension from the URL
    path = urlparse.urlparse(url).path
    split = os.path.splitext(path)
    ext = ""
    if len(split) >= 2:
        ext = split[1]

    # convert the temporary file into Django File with a random name and real extension (if found)
    django_file = File(img_temp)
    django_file.name = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(9)) + ext

    return django_file

def get_location_category():
    return LocationCategory.objects.all()



class SelectWithTitle(forms.Select):
    def __init__(self, attrs=None, choices=(), option_title_field=''):
        self.option_title_field = option_title_field
        super(SelectWithTitle, self).__init__(attrs, choices)

    def render_option(self, selected_choices, option_value, option_label, option_title=''):
        return u'<option value="%s" data-is-hike="%s">%s</option>' % (
            escape(option_value), escape(option_title), u'%s' % (option_label))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set(u'%s' % (v) for v in selected_choices)
        choices = [(c[0], c[1], '') for c in choices]
        more_choices = [(c[0], c[1]) for c in self.choices]
        try:
            option_title_list = [val_list[0] for val_list in self.choices.queryset.values_list(self.option_title_field)]
            if len(more_choices) > len(option_title_list):
                option_title_list = [''] + option_title_list # pad for empty label field
            more_choices = [(c[0], c[1], option_title_list[more_choices.index(c)]) for c in more_choices]
        except:
            more_choices = [(c[0], c[1], '') for c in more_choices] # couldn't get title values
        output = []
        for option_value, option_label, option_title in more_choices:
            output.append(self.render_option(selected_choices, option_value, option_label, option_title))
        return u'\n'.join(output)


class NewGoalForm(forms.ModelForm):
    image = forms.FileField(required=False)
    temp_image = forms.CharField(required=False)
    image_url = forms.CharField(label=_("Paste image URL here"), required=False)

    class Meta:
        model = Goal
        fields = ('title', 'description', 'tags', 'image', 'image_author', 'image_source')

    def __init__(self, *args, **kwargs):
        super(NewGoalForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(NewGoalForm, self).clean()
        temp_image = cleaned_data.get("temp_image")
        image = cleaned_data.get("image")
        image_url = cleaned_data.get("image_url")

        if not (temp_image or image or image_url):
            # image file nor image URL provided
            raise forms.ValidationError(_("Image file or URL must be specified"))

        if not temp_image and not image:
            try:
                cleaned_data["image"] = fetch_image(image_url)
            except FetchException, ex:
                raise forms.ValidationError(unicode(ex))
            except Exception:
                raise forms.ValidationError(_("Image cannot be fetched from the remote server, please try again or upload it from your computer"))

        return cleaned_data

    def save(self, commit=True):
        goal = super(NewGoalForm, self).save(commit=False)
        temp_image = self.cleaned_data.get("temp_image")
        image = self.cleaned_data.get("image")
        image_url = self.cleaned_data.get("image_url")

        if temp_image:
            # image already uploaded, use TemporaryImage
            image = TemporaryImage.objects.get(pk=temp_image)
            goal.image = image.image
        elif image:
            # image uploaded right now
            goal.image = image

        if commit:
            goal.save()

        return goal


class NewLocationGoalForm(NewGoalForm):
    site_url = forms.CharField(label=_("URL (optional)"), required=False)
    hike_detail = forms.CharField(label=_("Detail for Hike category"), required=False)
    address = forms.CharField(label=_("Search by name of location or enter address or pin location on map below."), required=False)
    neighborhood = forms.CharField(required=False)
    bounds = forms.CharField(required=False)
    place = forms.CharField(required=False)
    category = forms.ModelChoiceField(queryset=LocationCategory.objects.all(), widget=SelectWithTitle(attrs={'class': 'form-control'}, option_title_field='is_hike'))

    class Meta:
        model = Goal
        fields = ('title', 'description', 'tags', 'phone_number', 'image', 'image_author', 'image_source', 'category', 'site_url', 'hike_detail')

    def __init__(self, *args, **kwargs):
        super(NewGoalForm, self).__init__(*args, **kwargs)
        self.fields['category'].empty_label = None

    def clean(self):
        return super(NewLocationGoalForm, self).clean()

    def save(self, commit=True):
        return super(NewLocationGoalForm, self).save(commit)


class TemporaryImageForm(forms.ModelForm):
    image = forms.FileField(required=False)
    image_url = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(TemporaryImageForm, self).clean()
        image = cleaned_data.get("image")
        image_url = cleaned_data.get("image_url")

        if image or image_url:
            if image:
                # image file uploaded
                self.actual_image = image
            else:
                # image URL filled
                try:
                    self.actual_image = fetch_image(image_url)
                except FetchException, ex:
                    raise forms.ValidationError(unicode(ex))
                except Exception:
                    raise forms.ValidationError(_("Image cannot be fetched from the remote server, please try again or upload it from your computer"))
            return cleaned_data
        else:
            # image file nor image URL provided
            raise forms.ValidationError(_("Image file or URL must be specified"))

    def save(self, commit=True):
        temp_image = super(TemporaryImageForm, self).save(commit=False)
        temp_image.image = self.actual_image

        if commit:
            temp_image.save()

        return temp_image

    class Meta:
        model = TemporaryImage
        fields = ('image',)


class ContactForm(forms.Form):
    MESSAGE_TYPE = (
        ('bug', _('Report bug')),
        ('question', _('Questions')),
        ('comment', _('Comments')),
        ('suggestion', _('Suggestions')),
    )
    type = forms.ChoiceField(label=_("Type"), choices=MESSAGE_TYPE)
    name = forms.CharField(label=_("Name"), max_length=30)
    email = forms.EmailField(label=_('Email address'))
    message = forms.CharField(label=_('Message'), widget=forms.Textarea(attrs={'rows':5}))

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.form_id = 'contact_form'
        self.helper.add_input(Submit('submit', 'Submit!'))


class BoundsForm(forms.Form):
    top = forms.FloatField(min_value=-90, max_value=90)
    bottom = forms.FloatField(min_value=-90, max_value=90)
    left = forms.FloatField(min_value=-180, max_value=180)
    right = forms.FloatField(min_value=-180, max_value=180)
    zoom = forms.IntegerField(min_value=0, max_value=21, required=False)

    def get_polygon(self):
        if self.is_valid():
            from django.contrib.gis.geos import Polygon
            top = self.cleaned_data['top']
            bottom = self.cleaned_data['bottom']
            left = self.cleaned_data['left']
            right = self.cleaned_data['right']
            if left > right: # crossing dateline
                return MultiPolygon(Polygon.from_bbox((left, bottom, 180, top)), Polygon.from_bbox((-180, bottom, right, top)))
            else:
                return Polygon.from_bbox((left, bottom, right, top))
