import json
from smtplib import SMTPRecipientsRefused, SMTPException
from django.contrib.auth import get_user
from django.contrib import messages
from django.db import transaction
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib import comments
from django.contrib.comments.views.comments import CommentPostBadRequest
from django.utils.encoding import smart_text
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.html import escape
from django.shortcuts import render
from django.template import RequestContext
from rest_framework import viewsets, routers, status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from yoloify.pinboard.models import Pin, Goal, TemporaryImage
from yoloify.pinboard.forms import TemporaryImageForm, ContactForm
from yoloify.serializers import PinSerializer, GoalSerializer
from yoloify.signup.forms import PasswordChangeForm, PasswordResetForm, LoginForm, SignupForm, ConfirmationResendForm
from django.contrib import auth
from django.conf import settings
from rest_framework.exceptions import APIException
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from yoloify.pinboard.tasks import UserSpecificCache, ProfileGoalsCachedPinboard, ProfileCompletedCachedPinboard, get_cached_pinboard
from yoloify.pinboard import verbs as PinVerb
from yoloify.pinboard.pin_feedly import feedly
from yoloify.utils.views import send_signup_admin_notification


class GoalViewSet(viewsets.ModelViewSet):
    model = Goal
    serializer_class = GoalSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return get_user(self.request).goals.all()


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == get_user(request)


class PinViewSet(viewsets.ModelViewSet):
    model = Pin
    serializer_class = PinSerializer

    def pre_save(self, obj):
        obj.user = get_user(self.request)
        if obj.pk is None and obj.is_reposted_by(obj.user):
            raise APIException(detail="Already bookmarked")

    def post_save(self, obj, created=False):
        UserSpecificCache.update_repins(obj.user.id)
        ProfileGoalsCachedPinboard(target_user_id=obj.user.id).update()
        if not created:
            ProfileCompletedCachedPinboard(target_user_id=obj.user.id).update()

        return super(PinViewSet, self).post_save(obj, created=created)

    def destroy(self, request, pk=None):
        if pk is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        pin = Pin.objects.get(pk=pk)
        if pin.user != request.user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user = pin.user
        pin.delete()

        UserSpecificCache.update_repins(user.id)
        ProfileGoalsCachedPinboard(target_user_id=user.id).update()
        if pin.complete:
            ProfileCompletedCachedPinboard(target_user_id=user.id).update()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordChangeView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request, *args, **kwargs):
        form = PasswordChangeForm(user=get_user(request), data=request.DATA)
        if form.is_valid():
            form.save()
            return Response(_('Your password was changed.'))
        return Response(form.errors, status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = (AllowAny,)

    def patch(self, request, *args, **kwargs):
        form = PasswordResetForm(request.DATA)
        if form.is_valid():
            form.save()
            return Response(_('Reset e-mail was sent.'))
        return Response(form.errors, status.HTTP_400_BAD_REQUEST)


class ConfirmationResendView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        form = ConfirmationResendForm(request.DATA)
        if form.is_valid():
            form.save()
            return Response(_('Confirmation e-mail was resent.'))
        else:
            return Response(form.errors, status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('home'))

    def post(self, request, *args, **kwargs):
        form = LoginForm(data=request.DATA, request=request)
        if form.is_valid():
            auth.login(request, form.get_user())
            return Response("OK")
        return Response(form.errors, status.HTTP_400_BAD_REQUEST)


class SignupView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        with transaction.commit_manually():
            try:
                form = SignupForm(request.DATA)
                if form.is_valid():
                    user = form.save()
                    user.email_confirmation.send(update_timestamp=False)
                    messages.info(request, _('Confirmation email sent. Please check your mailbox.'))
                    if getattr(settings, 'ADMIN_SIGNUP_NOTIFICATION', False):
                        send_signup_admin_notification(user)
                    user.backend = settings.AUTHENTICATION_BACKENDS[0]
                    auth.login(request, user)
                    return Response("OK")
                return Response(form.errors, status.HTTP_400_BAD_REQUEST)
            except SMTPException:
                transaction.rollback()
                return Response({'__all__': [_("Couldn't send you a confirmation message.")]}, status.HTTP_400_BAD_REQUEST)
            except:
                transaction.rollback()
                raise
            finally:
                transaction.commit()



class ImageUploadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        form = TemporaryImageForm(request.POST, request.FILES)
        if form.is_valid():
            temp = form.save()
            return Response(temp.id)
        return Response(form.errors, status.HTTP_400_BAD_REQUEST)


class LikeView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        goal = Goal.objects.get(id=request.POST['goal_id'])
        try:
            pin = Pin.objects.get(user=request.user, goal=goal)
            liked = not pin.liked
            pin.liked = liked
            pin.liked_at = timezone.now()
            pin.save()
        except Pin.DoesNotExist:
            pin = Pin(user=request.user, goal=goal)
            pin.liked = True
            pin.liked_at = timezone.now()
            pin.save()
            liked = True

        UserSpecificCache.update_likes(request.user.id)
        if liked:
            goal.like_count += 1
            feedly.add_pin(pin, pin.user.id, PinVerb.Like)
        else:
            goal.like_count -= 1
        goal.save()

        return Response({
            "liked": liked,
            "count": goal.like_count
        })


class BookmarkView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        goal = Goal.objects.get(id=request.POST['goal_id'])
        try:
            pin = Pin.objects.get(user=request.user, goal=goal)
            bookmarked = not pin.bookmarked
            pin.bookmarked = bookmarked
            pin.bookmarked_at = timezone.now()
            pin.save()
        except Pin.DoesNotExist:
            pin = Pin(user=request.user, goal=goal)
            pin.bookmarked = True
            pin.bookmarked_at = timezone.now()
            pin.save()
            bookmarked = True

        UserSpecificCache.update_repins(request.user.id)
        get_cached_pinboard(
            'profile_goals',
            target_user_id=request.user.id,
        ).update()

        if bookmarked:
            goal.pin_count += 1
            feedly.add_pin(pin, pin.user.id, PinVerb.Add)
        else:
            goal.pin_count -= 1
        goal.save()

        return Response({
            "bookmarked": bookmarked,
            "count": goal.pin_count
        })


class CompletedView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        goal = Goal.objects.get(id=request.POST['goal_id'])
        try:
            pin = Pin.objects.get(user=request.user, goal=goal)
            complete = not pin.complete
            pin.complete = complete
            pin.complete_at = timezone.now()
            pin.save()
        except Pin.DoesNotExist:
            pin = Pin(user=request.user, goal=goal)
            pin.complete = True
            pin.complete_at = timezone.now()
            pin.save()
            complete = True

        get_cached_pinboard(
            'profile_completed',
            target_user_id=request.user.id,
        ).update()

        if complete:
            goal.complete_count += 1
            feedly.add_pin(pin, pin.user.id, PinVerb.Complete)
        else:
            goal.complete_count -= 1
        goal.save()

        return Response({
            "completed": complete,
            "count": goal.complete_count
        })


class ContactView(APIView):
    permission_classes = (IsAuthenticated, )

    def send_email(self, context):
        subject = render_to_string('contact/_contact_message_subject.txt')
        message = render_to_string('contact/_contact_message_body.txt', context)

        email = send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, settings.ADMINS)

        return email

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.DATA)
        if form.is_valid():
            try:
                context = {
                    'name': form.cleaned_data['name'],
                    'email': form.cleaned_data['email'],
                    'message': form.cleaned_data['message'],
                    'type': form.cleaned_data['type'],
                }
                self.send_email(context)
            except Exception, ex:
                Response('Try again!', status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response("Success")
        return Response(form.errors, status.HTTP_400_BAD_REQUEST)


class CommentView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self, ctype, object_pk):

        CommentModel = comments.get_model()

        if not object_pk:
            return CommentModel.objects.none()

        qs = CommentModel.objects.filter(
            content_type=ctype,
            object_pk=smart_text(object_pk),
            site__pk=settings.SITE_ID,
        )

        # The is_public and is_removed fields are implementation details of the
        # built-in comment model's spam filtering system, so they might not
        # be present on a custom comment model subclass. If they exist, we
        # should filter on them.
        field_names = [f.name for f in CommentModel._meta.fields]
        if 'is_public' in field_names:
            qs = qs.filter(is_public=True)
        if getattr(settings, 'COMMENTS_HIDE_REMOVED', True) and 'is_removed' in field_names:
            qs = qs.filter(is_removed=False)

        return qs

    def get(self, request):
        ctype = request.GET.get('content_type')
        object_pk = request.GET.get('object_pk')
        user = get_user(request)
        profile = user.get_profile() if user.is_authenticated() else None

        app, model = ctype.split('.')
        ctype = ContentType.objects.get_by_natural_key(app, model)

        obj = ctype.get_object_for_this_type(pk=object_pk)
        form = comments.get_form()(obj)
        all_comments = self.get_queryset(ctype, object_pk)
        
        html = render(request, 'pinboard/_pin_comment_form.html', {
            'comments': all_comments,
            'form': form,
            'profile': profile,
            'pin_id': request.GET.get('pin_id')
        })
        return HttpResponse(html, content_type="text/html")

    def post(self, request, *args, **kwargs):
        """
        Post a comment, via an Ajax call.
        """

        # This is copied from django.contrib.comments.

        # Fill out some initial data fields from an authenticated user
        data = request.POST.copy()
        if request.user.is_authenticated():
            if not data.get('name', ''):
                data["name"] = request.user.get_full_name() or request.user.username
            if not data.get('email', ''):
                data["email"] = request.user.email

        # Look up the object we're trying to comment about
        ctype = data.get("content_type")
        object_pk = data.get("object_pk")
        if ctype is None or object_pk is None:
            return CommentPostBadRequest("Missing content_type or object_pk field.")
        try:
            object_pk = long(object_pk)
            model = models.get_model(*ctype.split(".", 1))
            target = model._default_manager.get(pk=object_pk)
        except ValueError:
            return CommentPostBadRequest("Invalid object_pk value: {0}".format(escape(object_pk)))
        except TypeError:
            return CommentPostBadRequest("Invalid content_type value: {0}".format(escape(ctype)))
        except AttributeError:
            return CommentPostBadRequest("The given content-type {0} does not resolve to a valid model.".format(escape(ctype)))
        except ObjectDoesNotExist:
            return CommentPostBadRequest("No object matching content-type {0} and object PK {1} exists.".format(escape(ctype), escape(object_pk)))
        except (ValueError, ValidationError) as e:
            return CommentPostBadRequest("Attempting go get content-type {0!r} and object PK {1!r} exists raised {2}".format(escape(ctype), escape(object_pk), e.__class__.__name__))

        # Construct the comment form
        form = comments.get_form()(target, data=data)
        
        if form.errors:
            json_response = json.dumps(form.errors)
            return HttpResponse(json_response, content_type="application/json")

        # Otherwise create the comment
        comment = form.get_comment_object()
        comment.ip_address = request.META.get("REMOTE_ADDR", None)
        if request.user.is_authenticated():
            comment.user = request.user

        # Signal that the comment is about to be saved
        responses = comments.signals.comment_will_be_posted.send(
            sender  = comment.__class__,
            comment = comment,
            request = request
        )

        for (receiver, response) in responses:
            if response is False:
                return CommentPostBadRequest("comment_will_be_posted receiver {0} killed the comment".format(receiver.__name__))

        # Save the comment and signal that it was saved
        comment.save()
        # add an activity
        pin = Pin.objects.get(id=data['pin'])
        feedly.add_pin(pin, request.user.id, PinVerb.Comment)

        comments.signals.comment_was_posted.send(
            sender  = comment.__class__,
            comment = comment,
            request = request
        )

        html = render_to_string(
            'pinboard/_pin_single_comment.html',
            { 'comment': comment },
            context_instance=RequestContext(request)
        )

        json_return = {
            'html' : html,
            'total_comment' : target.comment_count
        }
        json_response = json.dumps(json_return)

        return HttpResponse(json_response, content_type="application/json")


class CommentFlagView(APIView):
    permission_classes = (IsAuthenticated, )

    def perform_flag(self, request, comment):
        """
        Actually perform the flagging of a comment from a request.
        """
        flag, created = comments.models.CommentFlag.objects.get_or_create(
            comment = comment,
            user    = request.user,
            flag    = comments.models.CommentFlag.SUGGEST_REMOVAL
        )
        comments.signals.comment_was_flagged.send(
            sender  = comment.__class__,
            comment = comment,
            flag    = flag,
            created = created,
            request = request,
        )

    def post(self, request,  *args, **kwargs):
        data = request.POST.copy()
        CommentModel = comments.get_model()

        try:
            comment = CommentModel.objects.get(pk=data['comment_id'])
        except CommentModel.DoesNotExist:
            raise Http404

        self.perform_flag(request, comment)

        return HttpResponse('Success')


router = routers.DefaultRouter()
router.register(r'goals', GoalViewSet)
router.register(r'pins', PinViewSet)
