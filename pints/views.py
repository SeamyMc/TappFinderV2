import json
import urllib.request
import urllib.parse
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Avg, Count, Min, Q
from .models import (
    Amenity,
    AmenityReport,
    Beer,
    Event,
    EventType,
    PintLog,
    Pub,
)


@ensure_csrf_cookie
def map_view(request):
    return render(request, 'pints/map.html')


@require_GET
def api_pubs(request):
    pubs = Pub.objects.annotate(
        log_count=Count('pint_logs'),
        avg_price=Avg('pint_logs__price'),
    )
    features = [
        {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [float(pub.longitude), float(pub.latitude)],
            },
            'properties': {
                'id': pub.id,
                'name': pub.name,
                'log_count': pub.log_count,
                'avg_price': round(float(pub.avg_price), 2) if pub.avg_price else None,
            },
        }
        for pub in pubs
    ]
    return JsonResponse({'type': 'FeatureCollection', 'features': features})


@require_GET
def api_pub_detail(request, pub_id):
    pub = get_object_or_404(Pub, id=pub_id)
    logs = (
        PintLog.objects
        .filter(pub=pub)
        .select_related('user', 'beer')
        .order_by('-logged_at')[:8]
    )
    return JsonResponse({
        'id': pub.id,
        'name': pub.name,
        'address': pub.address,
        'logs': [
            {
                'user': log.user.username,
                'beer': log.beer.name,
                'price': str(log.price),
                'serving_size': log.get_serving_size_display(),
                'logged_at': log.logged_at.strftime('%d %b %Y'),
            }
            for log in logs
        ],
    })


@require_GET
def api_geocode(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'results': []})
    params = urllib.parse.urlencode({'format': 'json', 'limit': 5, 'q': q})
    url = f'https://nominatim.openstreetmap.org/search?{params}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'TappFinder/1.0 (beer price crowd-sourcing app)',
        'Accept-Language': 'en',
    })
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        return JsonResponse({'results': data})
    except Exception:
        return JsonResponse({'results': []})


@require_GET
def api_beers(request):
    q = request.GET.get('q', '').strip()
    beers = Beer.objects.filter(name__icontains=q).values('id', 'name', 'image_url')[:20]
    return JsonResponse({'beers': list(beers)})


@require_GET
def api_beer_results(request):
    beer_name = request.GET.get('beer', '').strip()
    if not beer_name:
        return JsonResponse({'pubs': [], 'beer': '', 'found': False})

    beer = Beer.objects.filter(name__iexact=beer_name).first()
    if not beer:
        return JsonResponse({'pubs': [], 'beer': beer_name, 'found': False})

    pub_aggregates = (
        PintLog.objects
        .filter(beer=beer)
        .values('pub__id', 'pub__name', 'pub__address', 'pub__latitude', 'pub__longitude')
        .annotate(avg_price=Avg('price'), min_price=Min('price'), log_count=Count('id'))
        .order_by('avg_price')
    )

    pubs = []
    for p in pub_aggregates:
        recent_logs = (
            PintLog.objects
            .filter(beer=beer, pub_id=p['pub__id'])
            .select_related('user')
            .order_by('price')[:5]
        )
        pubs.append({
            'id': p['pub__id'],
            'name': p['pub__name'],
            'address': p['pub__address'] or '',
            'lat': float(p['pub__latitude']),
            'lng': float(p['pub__longitude']),
            'avg_price': round(float(p['avg_price']), 2),
            'min_price': round(float(p['min_price']), 2),
            'log_count': p['log_count'],
            'logs': [
                {
                    'price': str(log.price),
                    'serving_size': log.get_serving_size_display(),
                    'user': log.user.username,
                    'logged_at': log.logged_at.strftime('%d %b %Y'),
                }
                for log in recent_logs
            ],
        })

    return JsonResponse({'pubs': pubs, 'beer': beer.name, 'image_url': beer.image_url, 'found': True})


def pub_profile(request, pub_id):
    pub = get_object_or_404(Pub, id=pub_id)

    overall = PintLog.objects.filter(pub=pub).aggregate(
        total_logs=Count('id'),
        avg_price=Avg('price'),
        min_price=Min('price'),
    )

    beer_aggregates = (
        PintLog.objects
        .filter(pub=pub)
        .values('beer__id', 'beer__name', 'beer__image_url')
        .annotate(avg_price=Avg('price'), min_price=Min('price'), log_count=Count('id'))
        .order_by('avg_price')
    )

    beers = []
    for b in beer_aggregates:
        recent_logs = (
            PintLog.objects
            .filter(pub=pub, beer_id=b['beer__id'])
            .select_related('user')
            .order_by('price')[:3]
        )
        beers.append({
            'id': b['beer__id'],
            'name': b['beer__name'],
            'image_url': b['beer__image_url'] or '',
            'avg_price': round(float(b['avg_price']), 2),
            'min_price': round(float(b['min_price']), 2),
            'log_count': b['log_count'],
            'logs': [
                {
                    'price': str(log.price),
                    'serving_size': log.get_serving_size_display(),
                    'user': log.user.username,
                    'logged_at': log.logged_at.strftime('%d %b %Y'),
                }
                for log in recent_logs
            ],
        })

    amenities_ctx = _amenities_for_pub(pub, request.user)
    events_ctx = _upcoming_events_for_pub(pub)

    context = {
        'pub': pub,
        'beers': beers,
        'total_logs': overall['total_logs'] or 0,
        'avg_price': round(float(overall['avg_price']), 2) if overall['avg_price'] else None,
        'min_price': round(float(overall['min_price']), 2) if overall['min_price'] else None,
        'beer_count': len(beers),
        'amenities': amenities_ctx,
        'upcoming_events': events_ctx,
        'event_types': EventType.objects.filter(is_approved=True),
    }
    return render(request, 'pints/pub_profile.html', context)


def _amenities_for_pub(pub, user):
    reports = (
        AmenityReport.objects
        .filter(pub=pub)
        .values('amenity_id')
        .annotate(
            yes_count=Count('id', filter=Q(value=True)),
            no_count=Count('id', filter=Q(value=False)),
        )
    )
    tally_by_id = {r['amenity_id']: r for r in reports}

    user_votes = {}
    if user.is_authenticated:
        user_votes = dict(
            AmenityReport.objects
            .filter(pub=pub, user=user)
            .values_list('amenity_id', 'value')
        )

    result = []
    for amenity in Amenity.objects.filter(is_approved=True):
        tally = tally_by_id.get(amenity.id, {'yes_count': 0, 'no_count': 0})
        yes = tally['yes_count']
        no = tally['no_count']
        status = 'unknown'
        if yes or no:
            if yes > no:
                status = 'confirmed'
            elif no > yes:
                status = 'denied'
            else:
                status = 'contested'
        result.append({
            'id': amenity.id,
            'slug': amenity.slug,
            'name': amenity.name,
            'icon': amenity.icon,
            'description': amenity.description,
            'yes_count': yes,
            'no_count': no,
            'status': status,
            'user_vote': user_votes.get(amenity.id),  # True / False / None
        })
    # Confirmed first, then unknowns, then denied
    order = {'confirmed': 0, 'contested': 1, 'unknown': 2, 'denied': 3}
    result.sort(key=lambda a: (order[a['status']], -a['yes_count'], a['name']))
    return result


def _upcoming_events_for_pub(pub):
    now = timezone.now()
    # Recurring events always surface; one-offs only if in the future (with a small grace window).
    grace = now - timedelta(hours=4)
    events = (
        Event.objects
        .filter(pub=pub)
        .filter(Q(recurrence__in=['weekly', 'fortnightly', 'monthly']) | Q(starts_at__gte=grace))
        .select_related('event_type', 'created_by')
        .order_by('starts_at')[:20]
    )
    return events


def beer_profile(request, beer_id):
    beer = get_object_or_404(Beer, id=beer_id)

    overall = PintLog.objects.filter(beer=beer).aggregate(
        total_logs=Count('id'),
        avg_price=Avg('price'),
        min_price=Min('price'),
    )

    pub_aggregates = (
        PintLog.objects
        .filter(beer=beer)
        .values('pub__id', 'pub__name', 'pub__address', 'pub__latitude', 'pub__longitude')
        .annotate(avg_price=Avg('price'), min_price=Min('price'), log_count=Count('id'))
        .order_by('avg_price')
    )

    pubs = []
    for p in pub_aggregates:
        recent_logs = (
            PintLog.objects
            .filter(beer=beer, pub_id=p['pub__id'])
            .select_related('user')
            .order_by('price')[:3]
        )
        pubs.append({
            'id': p['pub__id'],
            'name': p['pub__name'],
            'address': p['pub__address'] or '',
            'lat': float(p['pub__latitude']),
            'lng': float(p['pub__longitude']),
            'avg_price': round(float(p['avg_price']), 2),
            'min_price': round(float(p['min_price']), 2),
            'log_count': p['log_count'],
            'logs': [
                {
                    'price': str(log.price),
                    'serving_size': log.get_serving_size_display(),
                    'user': log.user.username,
                    'logged_at': log.logged_at.strftime('%d %b %Y'),
                }
                for log in recent_logs
            ],
        })

    context = {
        'beer': beer,
        'pubs': pubs,
        'total_logs': overall['total_logs'] or 0,
        'avg_price': round(float(overall['avg_price']), 2) if overall['avg_price'] else None,
        'min_price': round(float(overall['min_price']), 2) if overall['min_price'] else None,
        'pub_count': len(pubs),
    }
    return render(request, 'pints/beer_profile.html', context)


@require_GET
def api_pub_autocomplete(request):
    q = request.GET.get('q', '').strip()
    pubs = Pub.objects.filter(name__icontains=q).order_by('name')[:15]
    return JsonResponse({'pubs': [{'id': p.id, 'name': p.name, 'address': p.address} for p in pubs]})


@require_GET
def api_pub_results(request):
    pub_id = request.GET.get('pub_id', '').strip()
    if not pub_id:
        return JsonResponse({'found': False})
    pub = get_object_or_404(Pub, id=pub_id)

    beer_aggregates = (
        PintLog.objects
        .filter(pub=pub)
        .values('beer__id', 'beer__name', 'beer__image_url')
        .annotate(avg_price=Avg('price'), min_price=Min('price'), log_count=Count('id'))
        .order_by('avg_price')
    )

    beers = []
    for b in beer_aggregates:
        recent_logs = (
            PintLog.objects
            .filter(pub=pub, beer_id=b['beer__id'])
            .select_related('user')
            .order_by('price')[:3]
        )
        beers.append({
            'name': b['beer__name'],
            'image_url': b['beer__image_url'] or '',
            'avg_price': round(float(b['avg_price']), 2),
            'min_price': round(float(b['min_price']), 2),
            'log_count': b['log_count'],
            'logs': [
                {
                    'price': str(log.price),
                    'serving_size': log.get_serving_size_display(),
                    'user': log.user.username,
                    'logged_at': log.logged_at.strftime('%d %b %Y'),
                }
                for log in recent_logs
            ],
        })

    return JsonResponse({
        'found': True,
        'pub': {
            'id': pub.id,
            'name': pub.name,
            'address': pub.address,
            'lat': float(pub.latitude),
            'lng': float(pub.longitude),
        },
        'beers': beers,
        'total_logs': sum(b['log_count'] for b in beers),
    })


@login_required
@require_POST
def api_add_pub(request):
    try:
        data = json.loads(request.body)
        pub = Pub.objects.create(
            name=data['name'].strip(),
            address=data.get('address', '').strip(),
            latitude=data['latitude'],
            longitude=data['longitude'],
            added_by=request.user,
        )
        return JsonResponse({'id': pub.id, 'name': pub.name})
    except (KeyError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def api_vote_amenity(request, pub_id):
    pub = get_object_or_404(Pub, id=pub_id)
    try:
        data = json.loads(request.body)
        slug = data['slug']
        vote = data['vote']  # 'yes', 'no', or 'clear'
    except (KeyError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)

    amenity = get_object_or_404(Amenity, slug=slug, is_approved=True)

    if vote == 'clear':
        AmenityReport.objects.filter(pub=pub, amenity=amenity, user=request.user).delete()
    elif vote in ('yes', 'no'):
        AmenityReport.objects.update_or_create(
            pub=pub, amenity=amenity, user=request.user,
            defaults={'value': vote == 'yes'},
        )
    else:
        return JsonResponse({'error': 'invalid vote'}, status=400)

    tally = AmenityReport.objects.filter(pub=pub, amenity=amenity).aggregate(
        yes=Count('id', filter=Q(value=True)),
        no=Count('id', filter=Q(value=False)),
    )
    user_vote = (
        AmenityReport.objects
        .filter(pub=pub, amenity=amenity, user=request.user)
        .values_list('value', flat=True).first()
    )
    return JsonResponse({
        'yes_count': tally['yes'],
        'no_count': tally['no'],
        'user_vote': user_vote,
    })


@login_required
@require_POST
def api_propose_amenity(request):
    try:
        data = json.loads(request.body)
        name = data['name'].strip()
        icon = data.get('icon', '').strip()[:8]
    except (KeyError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)

    if len(name) < 2 or len(name) > 60:
        return JsonResponse({'error': 'Name must be 2–60 chars.'}, status=400)

    slug = slugify(name)[:80]
    if not slug:
        return JsonResponse({'error': 'Invalid name.'}, status=400)

    existing = Amenity.objects.filter(Q(slug=slug) | Q(name__iexact=name)).first()
    if existing:
        return JsonResponse({
            'id': existing.id, 'slug': existing.slug, 'name': existing.name,
            'icon': existing.icon, 'is_approved': existing.is_approved, 'existed': True,
        })

    amenity = Amenity.objects.create(
        name=name, slug=slug, icon=icon,
        is_approved=False, created_by=request.user,
    )
    return JsonResponse({
        'id': amenity.id, 'slug': amenity.slug, 'name': amenity.name,
        'icon': amenity.icon, 'is_approved': amenity.is_approved, 'existed': False,
    })


@login_required
@require_POST
def api_create_event(request, pub_id):
    pub = get_object_or_404(Pub, id=pub_id)
    try:
        data = json.loads(request.body)
        event_type_slug = data['event_type']
        starts_at = data['starts_at']
        recurrence = data.get('recurrence', 'none')
        title = data.get('title', '').strip()[:200]
        description = data.get('description', '').strip()
    except (KeyError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)

    event_type = get_object_or_404(EventType, slug=event_type_slug, is_approved=True)

    starts_dt = timezone.datetime.fromisoformat(starts_at)
    if timezone.is_naive(starts_dt):
        starts_dt = timezone.make_aware(starts_dt)

    if recurrence not in dict(Event.RECURRENCE_CHOICES):
        return JsonResponse({'error': 'invalid recurrence'}, status=400)

    event = Event.objects.create(
        pub=pub,
        event_type=event_type,
        title=title,
        description=description,
        starts_at=starts_dt,
        recurrence=recurrence,
        created_by=request.user,
    )
    return JsonResponse({
        'id': event.id,
        'title': event.display_title,
        'event_type': event.event_type.name,
        'icon': event.event_type.icon,
        'starts_at': event.starts_at.isoformat(),
        'recurrence': event.recurrence,
        'description': event.description,
    })


@login_required
@require_POST
def api_delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if event.created_by_id != request.user.id and not request.user.is_staff:
        return JsonResponse({'error': 'forbidden'}, status=403)
    event.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_propose_event_type(request):
    try:
        data = json.loads(request.body)
        name = data['name'].strip()
        icon = data.get('icon', '').strip()[:8]
    except (KeyError, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)

    if len(name) < 2 or len(name) > 60:
        return JsonResponse({'error': 'Name must be 2–60 chars.'}, status=400)

    slug = slugify(name)[:80]
    if not slug:
        return JsonResponse({'error': 'Invalid name.'}, status=400)

    existing = EventType.objects.filter(Q(slug=slug) | Q(name__iexact=name)).first()
    if existing:
        return JsonResponse({
            'id': existing.id, 'slug': existing.slug, 'name': existing.name,
            'icon': existing.icon, 'is_approved': existing.is_approved, 'existed': True,
        })

    event_type = EventType.objects.create(
        name=name, slug=slug, icon=icon,
        is_approved=False, created_by=request.user,
    )
    return JsonResponse({
        'id': event_type.id, 'slug': event_type.slug, 'name': event_type.name,
        'icon': event_type.icon, 'is_approved': event_type.is_approved, 'existed': False,
    })


@login_required
@require_POST
def api_log_pint(request):
    try:
        data = json.loads(request.body)

        beer_name = data['beer'].strip()
        beer = Beer.objects.filter(name__iexact=beer_name).first()
        if not beer:
            beer = Beer.objects.create(name=beer_name, added_by=request.user)

        pub = get_object_or_404(Pub, id=data['pub_id'])
        price = Decimal(str(data['price']))

        log = PintLog.objects.create(
            user=request.user,
            pub=pub,
            beer=beer,
            price=price,
            serving_size=data.get('serving_size', 'pint'),
            notes=data.get('notes', '').strip(),
        )
        return JsonResponse({'id': log.id, 'success': True})
    except (KeyError, ValueError, InvalidOperation) as e:
        return JsonResponse({'error': str(e)}, status=400)
