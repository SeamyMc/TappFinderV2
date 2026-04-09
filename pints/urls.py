from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map'),
    path('api/pubs/', views.api_pubs, name='api_pubs'),
    path('api/pubs/<int:pub_id>/', views.api_pub_detail, name='api_pub_detail'),
    path('api/pubs/add/', views.api_add_pub, name='api_add_pub'),
    path('api/geocode/', views.api_geocode, name='api_geocode'),
    path('api/beers/', views.api_beers, name='api_beers'),
    path('api/beer-results/', views.api_beer_results, name='api_beer_results'),
    path('api/log/', views.api_log_pint, name='api_log_pint'),
]
