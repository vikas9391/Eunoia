from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')),  
    path('auth/', include('accounts.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('chatbot/', include('chatbot.urls')),  
    path('mood/', include('mood.urls')),  
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
