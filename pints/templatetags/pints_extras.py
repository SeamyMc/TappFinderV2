import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def safe_json(value):
    return mark_safe(
        json.dumps(value)
        .replace('<', '\\u003c')
        .replace('>', '\\u003e')
        .replace('&', '\\u0026')
        .replace('\u2028', '\\u2028')
        .replace('\u2029', '\\u2029')
    )

# Deterministic avatar background colour from a username string
_AVATAR_COLOURS = [
    '#b45309', '#92400e', '#78350f', '#7c3aed', '#6d28d9',
    '#2563eb', '#1d4ed8', '#0f766e', '#065f46', '#15803d',
    '#b91c1c', '#c2410c', '#0369a1', '#7e22ce', '#be185d',
]

@register.filter
def avatar_colour(username):
    idx = sum(ord(c) for c in str(username)) % len(_AVATAR_COLOURS)
    return _AVATAR_COLOURS[idx]
