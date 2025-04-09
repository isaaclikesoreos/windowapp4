"""
URL configuration for a_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from a_users.views import ProfileView
from a_home.views import *
from django.http import HttpResponseRedirect
from a_home import views as home_views
from a_home.views import quote_lookup_view
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),
    path('', home_views.home, name='home'),  # Default to home
    path('home/', home_views.home, name='home'),
    # In a_core/urls.py
    path('home/', include('a_home.urls')),  # Include a_home URLs
    path('accounts/', include('allauth.urls')),
    path('chat/', include('a_rtchat.urls')),
    path('profile/', include('a_users.urls')),
    path('windshields/', include('windshields.urls')),
    path('@<username>/', ProfileView.as_view(), name="profile"),
    path('administration/', include('a_administration.urls', namespace='a_administration')),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

