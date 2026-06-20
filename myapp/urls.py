from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),               
    path('Home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('About/', views.about, name='about'),
    path('Calminggg/', views.calminggg, name='calminggg'),
    path('Edoc/', views.edoc, name='edoc'),
    path('index/', views.index, name='index'),        
    path('forgotpassword/', views.forgot, name='forgotpassword'),
    path('qu/', views.qu, name='qu'),
    path('selfassesment/', views.self_assessment, name='selfassesment'),
    path('List/', views.list_page, name='list'),
    path('mood/', views.mood, name='mood'),
    path('login/', views.login, name='login'),
    path("mood/", views.mood, name="mood"),
    path("mood/clear/", views.clear_mood_history, name="clear_mood_history"),

]
