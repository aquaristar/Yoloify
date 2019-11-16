from django.contrib.auth import get_user
from django.shortcuts import render, redirect
from yoloify.pages.models import StaticPage
from django.shortcuts import get_object_or_404


def home(request):
    if get_user(request).is_authenticated():
        return redirect('local')
    return render(request, 'pages/home.html')
    
def fb_home(request):
    if get_user(request).is_authenticated():
        return redirect('local')
    return render(request, 'pages/fb.html')    
    
    
def about(request):
    return render(request, 'pages/about.html')   


def page(request, slug):
    static_page = get_object_or_404(StaticPage, slug=slug)
    return render(request, 'pages/static.html', {
        'page': static_page
    })


def divide_by_zero(request):
    """Good for testing 500 error handler when set DEBUG=False."""
    1987 / 0