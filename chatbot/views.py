import os
import json
import traceback
from typing import Any
from groq import Groq
from dotenv import load_dotenv
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import ChatSession, Message
from mood.models import Mood

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
GROQ_MODEL = "llama-3.3-70b-versatile"


def get_system_prompt(session: ChatSession, mood=None, user=None) -> str:
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

    if mood:
        base_prompt += f"\n\nThe user is currently feeling {mood}. "
        base_prompt += "Respond in a supportive, understanding, and friendly way that matches their mood. "

    if user:
        recent_moods = get_recent_moods(user)
        if recent_moods:
            base_prompt += f"\n\n{recent_moods} Respond empathetically considering their mood history."

    return session.system_prompt or base_prompt  # type: ignore[attr-defined]


def get_recent_moods(user, limit=5):
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
    return JsonResponse({"session_id": session.id})  # type: ignore[attr-defined]


@login_required
def get_chat_sessions(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by("-created_at")
    data = []
    for s in sessions:
        last_message = s.messages.last()  # type: ignore[attr-defined]
        data.append({
            "session_id": s.id,  # type: ignore[attr-defined]
            "title": s.title,
            "last_message": last_message.content if last_message else "(empty chat)",
            "timestamp": s.updated_at.strftime("%Y-%m-%d %H:%M"),
        })
    return JsonResponse({"sessions": data})


@login_required
def get_chat_by_id(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    chats = session.messages.all().order_by("created_at")  # type: ignore[attr-defined]
    conversation = [
        {"role": msg.role, "text": msg.content, "time": msg.created_at.strftime("%H:%M")}
        for msg in chats
    ]
    return JsonResponse({"conversation": conversation, "session_id": session.id})  # type: ignore[attr-defined]


@csrf_exempt
@login_required
def send_message(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
        user_input = data.get("message", "")
        session_id = data.get("session_id")
        attachments = data.get("attachments", [])

        if (not user_input and not attachments) or not session_id:
            return JsonResponse({"error": "Missing input"}, status=400)

        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        except ChatSession.DoesNotExist:
            return JsonResponse({"error": "Session not found"}, status=404)

        if not session.title or session.title.strip() in ["New Chat", "Untitled"]:
            if user_input:
                session.title = user_input.strip()[:30]
                session.save(update_fields=["title"])

        # Build messages for Groq
        history: list[Any] = [
            {"role": m.role, "content": m.content}
            for m in session.messages.order_by("-created_at")[:20][::-1]  # type: ignore[attr-defined]
        ]

        system_prompt = get_system_prompt(session, user=request.user)
        messages: list[Any] = [{"role": "system", "content": system_prompt}] + history

        if attachments:
            attachment_note = f"[User sent {len(attachments)} attachment(s) — image analysis not supported]"
            messages.append({
                "role": "user",
                "content": f"{user_input}\n{attachment_note}" if user_input else attachment_note
            })
        else:
            messages.append({"role": "user", "content": user_input})

        # Groq API call
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        reply = completion.choices[0].message.content

        # Save messages
        if user_input:
            Message.objects.create(session=session, role="user", content=user_input)
        if attachments and not user_input:
            Message.objects.create(session=session, role="user", content=f"[{len(attachments)} attachment(s)]")

        assistant_msg = Message.objects.create(session=session, role="assistant", content=reply)
        session.updated_at = assistant_msg.created_at
        session.save(update_fields=["updated_at"])

        return JsonResponse({
            "response": reply,
            "session_id": session.id,  # type: ignore[attr-defined]
            "message_id": assistant_msg.id,  # type: ignore[attr-defined]
            "session_title": session.title,
        })

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
    return JsonResponse({"session_id": session.id, "title": session.title})  # type: ignore[attr-defined]


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
        session.messages.all().delete()  # type: ignore[attr-defined]
        session.updated_at = timezone.now()
        session.save(update_fields=["updated_at"])
        return JsonResponse({"success": True, "message": "Session history cleared"})
    except Exception as ex:
        return JsonResponse({"error": str(ex)}, status=500)