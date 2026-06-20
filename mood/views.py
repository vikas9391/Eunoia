from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .models import Mood

@csrf_exempt
@login_required
def add_mood(request):
    if request.method == "POST":
        data = json.loads(request.body)
        mood = data.get("mood")
        if mood:
            Mood.objects.create(user=request.user, mood=mood)
            return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)

@login_required
def get_moods(request):
    moods = Mood.objects.filter(user=request.user).order_by("-timestamp")
    data = [
        {"mood": m.mood, "timestamp": m.timestamp.isoformat()}  # ISO format for JS
        for m in moods
    ]
    return JsonResponse(data, safe=False)

@csrf_exempt
@login_required
def clear_moods(request):
    if request.method == "POST":
        Mood.objects.filter(user=request.user).delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)
