from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm
from .security import clear_login_attempts, login_throttled, register_login_attempt


def _role_redirect(user):
    if user.is_staff:
        return redirect('admin-dashboard')
    return redirect('homepage')


def register_user(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, "User registered successfully")
            return redirect('login')
        messages.add_message(request, messages.ERROR, "User registration failed")
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_user(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            throttle_key = f"{request.META.get('REMOTE_ADDR')}:{data['username']}".lower()
            if login_throttled(throttle_key):
                messages.add_message(
                    request, messages.ERROR,
                    "Too many failed attempts. Please try again in a few minutes.",
                )
            else:
                user = authenticate(username=data['username'], password=data['password'])
                if user is not None:
                    clear_login_attempts(throttle_key)
                    login(request, user)
                    return _role_redirect(user)
                register_login_attempt(throttle_key)
                messages.add_message(request, messages.ERROR, "Invalid username or password")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@require_POST
def logout_user(request):
    logout(request)
    return redirect('homepage')
