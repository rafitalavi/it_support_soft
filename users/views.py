from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import LoginForm


def login_view(request):
    """
    Renders Square login portal and authenticates users using user_id and password.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            display_name = user.name if hasattr(user, 'name') and user.name else user.user_id
            messages.success(request, f"Welcome back, {display_name}!")

            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid User ID or password. Please verify your credentials.")
    else:
        form = LoginForm(request)

    return render(request, 'login.html', {'form': form, 'next': next_url})


def logout_view(request):
    """
    Logs out user and redirects to login screen.
    """
    if request.user.is_authenticated:
        display_name = request.user.name if hasattr(request.user, 'name') and request.user.name else request.user.user_id
        logout(request)
        messages.info(request, f"Goodbye {display_name}, you have been securely logged out.")
    return redirect('login')
