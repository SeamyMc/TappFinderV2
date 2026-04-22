from django.contrib import admin

from .models import (
    Amenity,
    AmenityReport,
    Beer,
    Contribution,
    Event,
    EventConfirmation,
    EventType,
    PintLog,
    Pub,
)


@admin.register(Pub)
class PubAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'added_by', 'created_at')
    search_fields = ('name', 'address')


@admin.register(Beer)
class BeerAdmin(admin.ModelAdmin):
    list_display = ('name', 'added_by', 'created_at')
    search_fields = ('name',)


@admin.register(PintLog)
class PintLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'beer', 'pub', 'price', 'serving_size', 'logged_at', 'is_seeded')
    list_filter = ('serving_size', 'is_seeded')
    search_fields = ('user__username', 'beer__name', 'pub__name')


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_approved', 'created_by', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(AmenityReport)
class AmenityReportAdmin(admin.ModelAdmin):
    list_display = ('pub', 'amenity', 'user', 'value', 'updated_at')
    list_filter = ('value', 'amenity')
    search_fields = ('pub__name', 'amenity__name', 'user__username')


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_approved', 'created_by', 'created_at')
    list_filter = ('is_approved',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('display_title', 'pub', 'event_type', 'starts_at', 'recurrence', 'created_by')
    list_filter = ('recurrence', 'event_type')
    search_fields = ('pub__name', 'title', 'event_type__name')
    date_hierarchy = 'starts_at'


@admin.register(EventConfirmation)
class EventConfirmationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'still_happening', 'updated_at')
    list_filter = ('still_happening',)


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind', 'pub', 'summary', 'created_at')
    list_filter = ('kind',)
    search_fields = ('user__username', 'pub__name')
    date_hierarchy = 'created_at'
    raw_id_fields = ('user', 'pub', 'pint_log', 'amenity_report', 'event', 'event_confirmation')
    readonly_fields = ('created_at',)
