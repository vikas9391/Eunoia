from django.urls import path
from . import views

urlpatterns = [
    path("api/moods/add/", views.add_mood, name="add_mood"),
    path("api/moods/get/", views.get_moods, name="get_moods"),
    path("api/moods/clear/", views.clear_moods, name="clear_moods"),
]
