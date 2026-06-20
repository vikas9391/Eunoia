from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_page, name='login_page'),
    path('signup/', views.signup_page, name='signup_page'),
    path('logout/', views.logout_page, name='logout_page'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),

    # Forgot Password Flow
    path('forgotpassword/', auth_views.PasswordResetView.as_view(
        template_name='forgotpassword.html',
        email_template_name='registration/password_reset_email.html',
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),

    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),  # ✅ important fix
    ), name='password_reset_confirm'),

    
]
