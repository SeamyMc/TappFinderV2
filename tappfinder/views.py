from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def home(request):
    if request.user.is_authenticated:
        return redirect('map')
    return render(request, 'home.html')


@login_required
def profile(request):
    return render(request, 'profile.html')


@login_required
def search(request):
    return render(request, 'search.html')
