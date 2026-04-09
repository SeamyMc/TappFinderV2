import json
import urllib.request
import urllib.parse
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Avg, Count, Min
from .models import Pub, Beer, PintLog


@ensure_csrf_cookie
@login_required
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
    beers = Beer.objects.filter(name__icontains=q).values('name', 'image_url')[:20]
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
