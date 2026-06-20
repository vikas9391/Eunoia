from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Mood


@login_required
def mood(request):
    if request.method == "POST":
        mood_value = request.POST.get("mood")
        if mood_value:
            Mood.objects.create(user=request.user, mood=mood_value)
        return redirect("mood")

    moods = Mood.objects.filter(user=request.user).order_by("-timestamp")
    return render(request, "mood.html", {"moods": moods})


@login_required
def clear_mood_history(request):
    if request.method == "POST":
        Mood.objects.filter(user=request.user).delete()
        return JsonResponse({"status": "success"})
    return HttpResponseBadRequest("POST required")


def index(request):
    return render(request, 'index.html')

def home(request):
    return render(request, 'Home.html')

def about(request):
    return render(request, 'About.html')

def login(request):
    return render(request, 'login.html')

def signup(request):
    return render(request, 'Signup.html')

def forgot(request):
    return render(request, 'forgotpassword.html')

def calminggg(request):
    return render(request, 'Calminggg.html')

def edoc(request):
    return render(request, 'Edoc.html')

def self_assessment(request):
    return render(request, 'selfassesment.html')

def qu(request):
    return render(request, 'qu.html')

def list_page(request):
    return render(request, 'List.html')