from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from pints.models import PintLog
from accounts.models import UserProfile


def home(request):
    if request.user.is_authenticated:
        return redirect('map')
    return render(request, 'home.html')


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html', {'profile': profile})


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
