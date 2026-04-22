from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map'),
    path('api/pubs/', views.api_pubs, name='api_pubs'),
    path('api/pubs/search/', views.api_pub_autocomplete, name='api_pub_autocomplete'),
    path('api/pubs/add/', views.api_add_pub, name='api_add_pub'),
    path('api/pubs/<int:pub_id>/', views.api_pub_detail, name='api_pub_detail'),
    path('api/pub-results/', views.api_pub_results, name='api_pub_results'),
    path('api/geocode/', views.api_geocode, name='api_geocode'),
    path('api/beers/', views.api_beers, name='api_beers'),
    path('api/beer-results/', views.api_beer_results, name='api_beer_results'),
    path('api/log/', views.api_log_pint, name='api_log_pint'),
    path('api/pubs/<int:pub_id>/amenities/vote/', views.api_vote_amenity, name='api_vote_amenity'),
    path('api/amenities/propose/', views.api_propose_amenity, name='api_propose_amenity'),
    path('api/pubs/<int:pub_id>/events/create/', views.api_create_event, name='api_create_event'),
    path('api/events/<int:event_id>/delete/', views.api_delete_event, name='api_delete_event'),
    path('api/event-types/propose/', views.api_propose_event_type, name='api_propose_event_type'),
]
