from django.urls import path
from . import views

urlpatterns = [
    path("", views.chatbot_view, name="chatbot"),
    
    # API endpoints
    path("api/chat/send/", views.send_message, name="send_message"),
    path("api/chat/new/", views.new_chat, name="new_chat"),
    path("api/chat/sessions/", views.get_chat_sessions, name="get_chat_sessions"),
    path("api/chat/messages/<int:session_id>/", views.get_chat_by_id, name="get_chat_by_id"),
    path("api/chat/session/<int:session_id>/rename/", views.rename_session, name="rename_session"),
    path("api/chat/session/<int:session_id>/delete/", views.delete_session, name="delete_session"),
    path("api/chat/session/<int:session_id>/clear/", views.clear_session, name="clear_session"),  # ✅ Added
]
