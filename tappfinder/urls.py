"""
URL configuration for tappfinder project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from . import views
from pints import views as pints_views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('profile/avatar/', views.upload_avatar, name='upload_avatar'),
    path('search/', views.search, name='search'),
    path('feed/', views.feed, name='feed'),
    path('beers/<int:beer_id>/', pints_views.beer_profile, name='beer_profile'),
    path('pubs/<int:pub_id>/', pints_views.pub_profile, name='pub_profile'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('map/', include('pints.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
