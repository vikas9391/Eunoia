import re
import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.views.decorators.cache import never_cache
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse


def login_page(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('pass')

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('home')
                else:
                    messages.error(request, "Account inactive. Please verify your email.")
            else:
                messages.error(request, "Invalid email or password.")
        except User.DoesNotExist:
            messages.error(request, "User with this email does not exist.")

        return render(request, 'login.html')

    return render(request, 'login.html')


def signup_page(request):
    logout(request)
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('pass')
        confirm_pass = request.POST.get('confirm_pass')

        if password != confirm_pass:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'signup.html')
        if not re.search(r'[A-Z]', password):
            messages.error(request, "Password must include an uppercase letter.")
            return render(request, 'signup.html')
        if not re.search(r'[a-z]', password):
            messages.error(request, "Password must include a lowercase letter.")
            return render(request, 'signup.html')
        if not re.search(r'[0-9]', password):
            messages.error(request, "Password must include a digit.")
            return render(request, 'signup.html')
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            messages.error(request, "Password must include a special character.")
            return render(request, 'signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, 'signup.html')

        try:
            user = User.objects.create_user(username=username, email=email, password=password, is_active=False)
            user.save()

            current_site = get_current_site(request)
            subject = 'Activate Your Eunoia Account'
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"http://{current_site.domain}/auth/activate/{uid}/{token}/"

            message = render_to_string('activate_email.html', {
                'user': user,
                'activation_link': activation_link,
            })

            from_email = os.getenv('DEFAULT_FROM_EMAIL', 'onboarding@resend.dev')
            email_msg = EmailMultiAlternatives(subject, '', from_email, [user.email])
            email_msg.attach_alternative(message, "text/html")
            email_msg.send()

            messages.success(request, "Account created! Check your email to activate your account.")
            return redirect('login_page')
        except IntegrityError:
            messages.error(request, "Username already exists. Try a different one.")
            return render(request, 'signup.html')
        except Exception as e:
            print("Unexpected Error:", e)
            messages.error(request, "Something went wrong while creating your account.")
            return render(request, 'signup.html')

    return render(request, 'signup.html')


def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated. You can now log in.")
        return redirect('login_page')
    else:
        return HttpResponse('Activation link is invalid or expired.')


def logout_page(request):
    logout(request)
    request.session.flush()
    return redirect('index')


@never_cache
@login_required(login_url='login_page')
def home(request):
    return render(request, 'home.html', {'user': request.user})