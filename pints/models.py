from django.db import models
from django.contrib.auth.models import User


class Pub(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=500, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    added_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='pubs_added')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Beer(models.Model):
    name = models.CharField(max_length=200, unique=True)
    image_url = models.URLField(max_length=500, blank=True)
    added_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='beers_added')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PintLog(models.Model):
    SERVING_SIZES = [
        ('pint', 'Pint'),
        ('half', 'Half'),
        ('third', 'Third'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pint_logs')
    pub = models.ForeignKey(Pub, on_delete=models.CASCADE, related_name='pint_logs')
    beer = models.ForeignKey(Beer, on_delete=models.CASCADE, related_name='pint_logs')
    price = models.DecimalField(max_digits=5, decimal_places=2)
    serving_size = models.CharField(max_length=10, choices=SERVING_SIZES, default='pint')
    notes = models.TextField(blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)
    is_seeded = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.user.username} — {self.beer.name} at {self.pub.name} (£{self.price})"


class Amenity(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    icon = models.CharField(max_length=8, blank=True)
    description = models.CharField(max_length=200, blank=True)
    is_approved = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='amenities_proposed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'amenities'

    def __str__(self):
        return self.name


class AmenityReport(models.Model):
    pub = models.ForeignKey(Pub, on_delete=models.CASCADE, related_name='amenity_reports')
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='amenity_reports')
    value = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['pub', 'amenity', 'user'], name='unique_amenity_report_per_user'),
        ]
        indexes = [models.Index(fields=['pub', 'amenity'])]

    def __str__(self):
        verdict = 'yes' if self.value else 'no'
        return f'{self.user.username}: {self.amenity.name} @ {self.pub.name} = {verdict}'


class EventType(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    icon = models.CharField(max_length=8, blank=True)
    description = models.CharField(max_length=200, blank=True)
    is_approved = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='event_types_proposed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Event(models.Model):
    RECURRENCE_CHOICES = [
        ('none', 'One-off'),
        ('weekly', 'Weekly'),
        ('fortnightly', 'Fortnightly'),
        ('monthly', 'Monthly'),
    ]

    pub = models.ForeignKey(Pub, on_delete=models.CASCADE, related_name='events')
    event_type = models.ForeignKey(EventType, on_delete=models.PROTECT, related_name='events')
    title = models.CharField(max_length=200, blank=True, help_text='Optional override; defaults to event type name.')
    description = models.TextField(blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    recurrence = models.CharField(max_length=16, choices=RECURRENCE_CHOICES, default='none')
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='events_added')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['starts_at']
        indexes = [models.Index(fields=['pub', 'starts_at'])]

    def __str__(self):
        return f'{self.display_title} @ {self.pub.name} ({self.starts_at:%Y-%m-%d %H:%M})'

    @property
    def display_title(self):
        return self.title or self.event_type.name


class EventConfirmation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='confirmations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_confirmations')
    still_happening = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'user'], name='unique_event_confirmation_per_user'),
        ]


class Contribution(models.Model):
    KIND_PINT = 'pint'
    KIND_AMENITY = 'amenity'
    KIND_EVENT = 'event'
    KIND_CONFIRMATION = 'confirmation'
    KIND_CHOICES = [
        (KIND_PINT, 'Price & Pint'),
        (KIND_AMENITY, 'Added Amenity'),
        (KIND_EVENT, 'Added Event'),
        (KIND_CONFIRMATION, 'Confirming'),
    ]
    POINTS = {
        KIND_PINT: 10,
        KIND_AMENITY: 5,
        KIND_EVENT: 5,
        KIND_CONFIRMATION: 1,
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contributions')
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, db_index=True)
    pub = models.ForeignKey(Pub, null=True, blank=True, on_delete=models.CASCADE, related_name='contributions')
    pint_log = models.OneToOneField(PintLog, null=True, blank=True, on_delete=models.CASCADE, related_name='contribution')
    amenity_report = models.OneToOneField(AmenityReport, null=True, blank=True, on_delete=models.CASCADE, related_name='contribution')
    event = models.OneToOneField(Event, null=True, blank=True, on_delete=models.CASCADE, related_name='contribution')
    event_confirmation = models.OneToOneField(EventConfirmation, null=True, blank=True, on_delete=models.CASCADE, related_name='contribution')
    created_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['kind', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} • {self.get_kind_display()} • {self.created_at:%Y-%m-%d}'

    @property
    def points(self):
        return self.POINTS.get(self.kind, 0)

    @property
    def summary(self):
        if self.kind == self.KIND_PINT and self.pint_log_id:
            log = self.pint_log
            return f'{log.beer.name} (£{log.price})'
        if self.kind == self.KIND_AMENITY and self.amenity_report_id:
            r = self.amenity_report
            return f'{r.amenity.name}: {"yes" if r.value else "no"}'
        if self.kind == self.KIND_EVENT and self.event_id:
            return self.event.display_title
        if self.kind == self.KIND_CONFIRMATION:
            if self.amenity_report_id:
                r = self.amenity_report
                return f'{r.amenity.name}: {"yes" if r.value else "no"}'
            if self.event_confirmation_id:
                c = self.event_confirmation
                verb = 'still on' if c.still_happening else 'cancelled'
                return f'{c.event.display_title} — {verb}'
        return ''
