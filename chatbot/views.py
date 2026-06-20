import os
import json
import requests
import traceback
from dotenv import load_dotenv
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import ChatSession, Message
from mood.models import Mood


# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")  
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"



def get_system_prompt(session, mood=None, user=None):
    base_prompt = (
        "You are a warm, friendly, and caring AI assistant. "
        "You always talk like a supportive best friend, showing empathy, positivity, and kindness. "
        "Use a gentle tone and emojis where appropriate to make the conversation feel personal and comforting.\n\n"
        "Specialized topics:\n"
        "1. Medical guidance (general health, symptoms, first aid, medicines, doctor advice).\n"
        "2. Emotional support (stress, motivation, positivity, empathy, coping with feelings).\n"
        "3. Basic everyday information (time, greetings, simple facts).\n\n"
        "Rules:\n"
        "- Do NOT answer questions outside these topics.\n"
        "- If asked something irrelevant (e.g., coding, politics, math), politely say:\n"
        "\"I can only help with medical, emotional support, and basic daily information 🙂🧠💊\"\n"
        "- Always reply in a kind, friendly, and empathetic tone."
    )

    # Add current mood
    if mood:
        base_prompt += f"\n\nThe user is currently feeling {mood}. "
        base_prompt += "Respond in a supportive, understanding, and friendly way that matches their mood. "

    # Add recent mood history
    if user:
        recent_moods = get_recent_moods(user)
        if recent_moods:
            base_prompt += f"\n\n{recent_moods} Respond empathetically considering their mood history."

    return session.system_prompt or base_prompt

def get_recent_moods(user, limit=5):
    """
    Fetch the last `limit` moods for the logged-in user.
    Returns a formatted string for the AI system prompt.
    """
    moods = Mood.objects.filter(user=user).order_by("-timestamp")[:limit]
    if not moods:
        return None
    mood_str = ", ".join([f"{m.mood} ({m.timestamp.strftime('%d/%m %I:%M %p')})" for m in moods])
    return f"Recent moods: {mood_str}."



@ensure_csrf_cookie
@login_required
def chatbot_view(request):
    return render(request, "chat.html")


@login_required
def new_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    session = ChatSession.objects.create(user=request.user)
    return JsonResponse({"session_id": session.id})


@login_required
def get_chat_sessions(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by("-created_at")
    data = []
    for s in sessions:
        last_message = s.messages.last()
        data.append({
            "session_id": s.id,
            "title": s.title,
            "last_message": last_message.content if last_message else "(empty chat)",
            "timestamp": s.updated_at.strftime("%Y-%m-%d %H:%M"),
        })
    return JsonResponse({"sessions": data})


@login_required
def get_chat_by_id(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    chats = session.messages.all().order_by("created_at")
    conversation = []
    for msg in chats:
        conversation.append({
            "role": msg.role,
            "text": msg.content,
            "time": msg.created_at.strftime("%H:%M"),
        })
    return JsonResponse({"conversation": conversation, "session_id": session.id})

@csrf_exempt
@login_required
def send_message(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
        print("📩 Incoming data:", data)  # DEBUG

        user_input = data.get("message", "")
        session_id = data.get("session_id")
        attachments = data.get("attachments", [])

        if (not user_input and not attachments) or not session_id:
            return JsonResponse({"error": "Missing input"}, status=400)

        # Fetch session
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return JsonResponse({"error": "Session not found"}, status=404)

        # ✅ Update session title in real-time if empty or default
        if not session.title or session.title.strip() in ["New Chat", "Untitled"]:
            if user_input:
                session.title = user_input.strip()[:30]  # truncate to 30 chars
                session.save(update_fields=["title"])

        # Fetch last 20 messages
        history = [{"role": m.role, "content": m.content} for m in session.messages.order_by("-created_at")[:20][::-1]]

        # System prompt + history
        prompt = get_system_prompt(session, user=request.user)
        messages = [{"role": "system", "content": prompt}] + history

        # User message + attachments
        user_parts = [{"text": user_input}] if user_input else []
        safe_attachments = []
        for att in attachments:
            mime = (att.get("mime_type") or "").lower()
            if att.get("data_base64") and mime.startswith("image/"):
                safe_attachments.append({"inlineData": {"mimeType": mime, "data": att["data_base64"]}})
            elif att.get("file_uri") and att.get("mime_type"):
                safe_attachments.append({"fileData": {"fileUri": att["file_uri"], "mimeType": att["mime_type"]}})
        messages.append({"role": "user", "parts": user_parts + safe_attachments})

        # Convert messages → Gemini format
        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            parts = m.get("parts") or ([{"text": m["content"]}] if "content" in m else [{"text": ""}])
            contents.append({"role": role, "parts": parts})

        body = {"contents": contents}

        # Gemini API call
        headers = {"Content-Type": "application/json"}
        params = {"key": GEMINI_API_KEY}
        response = requests.post(GEMINI_URL, headers=headers, params=params, json=body)
        print("🌐 Gemini Raw Response:", response.text[:500])  # DEBUG

        if response.status_code == 200:
            resp_json = response.json()
            gemini_reply = (
                resp_json.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "⚠️ No reply from Gemini")
            )

            # Save messages
            if user_input:
                Message.objects.create(session=session, role="user", content=user_input)
            if attachments and not user_input:
                Message.objects.create(session=session, role="user", content=f"[{len(attachments)} attachment(s)]")

            assistant_msg = Message.objects.create(session=session, role="assistant", content=gemini_reply)
            session.updated_at = assistant_msg.created_at
            session.save(update_fields=["updated_at"])

            return JsonResponse({
                "response": gemini_reply,
                "session_id": session.id,
                "message_id": assistant_msg.id,
                "session_title": session.title,  # <-- return updated title for frontend
            })

        else:
            return JsonResponse({"error": f"Gemini API error: {response.text}"}, status=response.status_code)

    except Exception as ex:
        print("🔥 ERROR in send_message:", str(ex))
        traceback.print_exc()
        return JsonResponse({"error": str(ex)}, status=500)


@login_required
def rename_session(request, session_id):
    if request.method != "PATCH":
        return JsonResponse({"error": "PATCH required"}, status=400)
    data = json.loads(request.body.decode("utf-8"))
    title = data.get("title")
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    if title:
        session.title = title
        session.save(update_fields=["title"])
    return JsonResponse({"session_id": session.id, "title": session.title})


@login_required
def delete_session(request, session_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "DELETE required"}, status=400)
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    session.delete()
    return JsonResponse({"deleted": True})

@csrf_exempt
@login_required
def clear_session(request, session_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "DELETE required"}, status=400)

    try:
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)

        # ✅ Delete all messages in this session
        session.messages.all().delete()

        # Update session timestamp
        session.updated_at = timezone.now()
        session.save(update_fields=["updated_at"])

        return JsonResponse({"success": True, "message": "Session history cleared"})
    except Exception as ex:
        return JsonResponse({"error": str(ex)}, status=500)
