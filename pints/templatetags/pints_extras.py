import json
from django import template

register = template.Library()

@register.filter
def safe_json(value):
    return json.dumps(value)

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
