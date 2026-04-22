from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    AmenityReport,
    Contribution,
    Event,
    EventConfirmation,
    PintLog,
)


@receiver(post_save, sender=PintLog)
def record_pint_contribution(sender, instance, created, **kwargs):
    if not created or instance.is_seeded:
        return
    Contribution.objects.create(
        user=instance.user,
        kind=Contribution.KIND_PINT,
        pub=instance.pub,
        pint_log=instance,
        created_at=instance.logged_at,
    )


@receiver(post_save, sender=AmenityReport)
def record_amenity_contribution(sender, instance, created, **kwargs):
    if not created:
        return
    others_exist = (
        AmenityReport.objects
        .filter(pub=instance.pub, amenity=instance.amenity)
        .exclude(pk=instance.pk)
        .exists()
    )
    kind = Contribution.KIND_CONFIRMATION if others_exist else Contribution.KIND_AMENITY
    Contribution.objects.create(
        user=instance.user,
        kind=kind,
        pub=instance.pub,
        amenity_report=instance,
        created_at=instance.created_at,
    )


@receiver(post_save, sender=Event)
def record_event_contribution(sender, instance, created, **kwargs):
    if not created or instance.created_by_id is None:
        return
    Contribution.objects.create(
        user=instance.created_by,
        kind=Contribution.KIND_EVENT,
        pub=instance.pub,
        event=instance,
        created_at=instance.created_at,
    )


@receiver(post_save, sender=EventConfirmation)
def record_event_confirmation_contribution(sender, instance, created, **kwargs):
    if not created:
        return
    Contribution.objects.create(
        user=instance.user,
        kind=Contribution.KIND_CONFIRMATION,
        pub=instance.event.pub,
        event_confirmation=instance,
        created_at=instance.created_at,
    )
