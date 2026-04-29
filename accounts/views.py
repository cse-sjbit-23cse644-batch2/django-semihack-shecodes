from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserLoginForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.get_full_name()}! You are registered as {user.get_role_display()}.')
            return redirect('dashboard_redirect')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect('dashboard_redirect')
        messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html', {'form': UserLoginForm()})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def dashboard_redirect(request):
    if request.user.role == 'faculty':
        return redirect('faculty_dashboard_combined')
    elif request.user.role == 'admin_bos':
        return redirect('admin_bos_dashboard_combined')
    elif request.user.role == 'hod':
        return redirect('hod_dashboard_combined')
    return redirect('login')