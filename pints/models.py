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

    class Meta:
        ordering = ['-logged_at']

    def __str__(self):
        return f"{self.user.username} — {self.beer.name} at {self.pub.name} (£{self.price})"
