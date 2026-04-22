from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from pints.models import Contribution, PintLog
from accounts.models import UserProfile


def home(request):
    if request.user.is_authenticated:
        return redirect('map')
    return render(request, 'home.html')


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    contributions = (
        Contribution.objects
        .filter(user=request.user)
        .select_related(
            'pub',
            'pint_log__beer',
            'amenity_report__amenity',
            'event__event_type',
            'event_confirmation__event__event_type',
            'event_confirmation__event__pub',
        )
        [:50]
    )

    totals = Contribution.objects.filter(user=request.user).aggregate(
        total=Count('id'),
        pints=Count('id', filter=Q(kind=Contribution.KIND_PINT)),
        amenities=Count('id', filter=Q(kind=Contribution.KIND_AMENITY)),
        events=Count('id', filter=Q(kind=Contribution.KIND_EVENT)),
        confirmations=Count('id', filter=Q(kind=Contribution.KIND_CONFIRMATION)),
    )

    score = (
        (totals['pints'] or 0) * Contribution.POINTS[Contribution.KIND_PINT]
        + (totals['amenities'] or 0) * Contribution.POINTS[Contribution.KIND_AMENITY]
        + (totals['events'] or 0) * Contribution.POINTS[Contribution.KIND_EVENT]
        + (totals['confirmations'] or 0) * Contribution.POINTS[Contribution.KIND_CONFIRMATION]
    )

    return render(request, 'profile.html', {
        'profile': profile,
        'contributions': contributions,
        'totals': totals,
        'score': score,
    })


@login_required
@require_POST
def upload_avatar(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if 'avatar' in request.FILES:
        if profile.avatar:
            profile.avatar.delete(save=False)
        profile.avatar = request.FILES['avatar']
        profile.save()
    return redirect('profile')


@login_required
def search(request):
    return render(request, 'search.html')


@login_required
def feed(request):
    logs = (
        PintLog.objects
        .select_related('user', 'pub', 'beer', 'user__profile')
        .order_by('-logged_at')[:100]
    )
    return render(request, 'feed.html', {'logs': logs})
