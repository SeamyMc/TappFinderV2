import json
import urllib.request
import urllib.parse
from django.core.management.base import BaseCommand, CommandError
from pints.models import Pub

# Bounding boxes (south, west, north, east) for common UK cities.
# Use --city to pick one, or --bbox to supply your own.
CITY_BBOXES = {
    'london':     (51.28, -0.51, 51.69,  0.33),
    'manchester': (53.33, -2.40, 53.55, -1.97),
    'birmingham': (52.38, -2.05, 52.60, -1.72),
    'leeds':      (53.70, -1.75, 53.88, -1.43),
    'liverpool':  (53.32, -3.07, 53.48, -2.84),
    'edinburgh':  (55.87, -3.35, 55.99, -3.10),
    'glasgow':    (55.79, -4.38, 55.92, -4.12),
    'bristol':    (51.39, -2.70, 51.52, -2.51),
    'sheffield':  (53.31, -1.60, 53.43, -1.38),
    'newcastle':  (54.93, -1.72, 55.02, -1.55),
    'cardiff':    (51.44, -3.25, 51.54, -3.13),
    'nottingham': (52.89, -1.23, 52.97, -1.10),
}

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'

QUERY_TEMPLATE = '''
[out:json][timeout:90];
(
  node["amenity"="pub"]({s},{w},{n},{e});
  way["amenity"="pub"]({s},{w},{n},{e});
);
out center tags {limit};
'''


class Command(BaseCommand):
    help = 'Seeds pubs from OpenStreetMap via the Overpass API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--city', type=str, default='london',
            help=f'City to import pubs from. Known cities: {", ".join(CITY_BBOXES)}',
        )
        parser.add_argument(
            '--bbox', type=str, default=None,
            help='Custom bounding box as "south,west,north,east" (overrides --city)',
        )
        parser.add_argument(
            '--limit', type=int, default=500,
            help='Max pubs to import (default: 500)',
        )

    def handle(self, *args, **options):
        if options['bbox']:
            try:
                s, w, n, e = [float(x) for x in options['bbox'].split(',')]
            except ValueError:
                raise CommandError('--bbox must be four comma-separated floats: south,west,north,east')
            label = options['bbox']
        else:
            key = options['city'].lower()
            if key not in CITY_BBOXES:
                raise CommandError(
                    f'Unknown city "{options["city"]}". '
                    f'Use one of: {", ".join(CITY_BBOXES)} or supply --bbox.'
                )
            s, w, n, e = CITY_BBOXES[key]
            label = options['city'].title()

        limit = options['limit']
        self.stdout.write(f'Querying OpenStreetMap for pubs in {label} (limit {limit})...')

        query = QUERY_TEMPLATE.format(s=s, w=w, n=n, e=e, limit=limit)
        payload = urllib.parse.urlencode({'data': query}).encode()
        req = urllib.request.Request(
            OVERPASS_URL,
            data=payload,
            headers={'User-Agent': 'TappFinder/1.0 (beer price crowd-sourcing app)'},
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
        except Exception as e:
            raise CommandError(f'Overpass API error: {e}')

        elements = result.get('elements', [])
        self.stdout.write(f'Found {len(elements)} pubs in OSM data')

        created = skipped = 0

        for el in elements:
            tags = el.get('tags', {})
            name = (tags.get('name') or '').strip()
            if not name:
                continue

            if el['type'] == 'node':
                lat, lng = el['lat'], el['lon']
            elif el['type'] == 'way' and 'center' in el:
                lat, lng = el['center']['lat'], el['center']['lon']
            else:
                continue

            parts = []
            number = tags.get('addr:housenumber', '')
            street = tags.get('addr:street', '')
            if number and street:
                parts.append(f'{number} {street}')
            elif street:
                parts.append(street)
            if tags.get('addr:city'):
                parts.append(tags['addr:city'])
            address = ', '.join(parts)

            if Pub.objects.filter(name__iexact=name).exists():
                skipped += 1
                continue

            Pub.objects.create(name=name, address=address, latitude=lat, longitude=lng)
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. {created} pubs added, {skipped} already existed.'
        ))
