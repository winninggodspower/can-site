import os
import subprocess
from django.shortcuts import render, redirect, resolve_url
from django.contrib import messages

# modules needed for user authentication
from django.contrib.auth import authenticate, login, logout

#for pasword reset
from django.db.models.query_utils import Q
from django.contrib.auth.views import PasswordResetView

from django.conf import settings

# importing the use model
from django.contrib.auth import get_user_model
User = get_user_model()


# importing the forms
from .forms import LoginForm, RegisterForm

# routes for user registration
def register(request):

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            # form.save only works when form is created from a model
            form.save()
            messages.success(request, 'succesfully created account')
            return redirect('/')
        else:
            # rendering the template again if the form is not valid with the prepopulated data.
            return render(request, 'signup.html', {'form': form})
    else:
        form = RegisterForm()
        return render(request, 'signup.html', {'form': form})
    

def login_user(request):
    # redirect user to home if already logged in
    if request.user.is_authenticated:
        messages.info(request, 'You Are Already Logged In')
        return redirect('/')

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            username = User.objects.filter(email = form.cleaned_data.get('email')).first()
            print(username)
            # the authenticate function returns the user object if the user is found else it returns none
            user = authenticate(username=username, password=form.cleaned_data.get('password'))
            if user:
                login(request, user)
                messages.success(request, f'successfully logged in as {user.username}')
                return redirect('course:dashboard')
            else:
                messages.error(request, 'Invalid credentials')
                return redirect('/login')

        # if form is not valid render the template again with pre populated data
        else:
            return render(request, 'login.html', {'form': form})
    else:
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

def login_admin_user(request):
    # redirect user to home if already logged in
    if request.user.is_authenticated:
        messages.info(request, 'You Are Already Logged In')
        return redirect('/admin')

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            print(form.cleaned_data)
            username = User.objects.filter(email = form.cleaned_data.get('email')).first()
            # the authenticate function returns the user object if the user is found else it returns none
            user = authenticate(username=username, password=form.cleaned_data.get('password'))
            if user and user.is_superuser:
                login(request, user)
                messages.success(request, f'successfully logged in as {user.username}')
                return redirect('/admin')
            else:
                messages.error(request, 'Invalid credentials')
                # form.add_error('user not found')
                return redirect('/login')

        # if form is not valid render the template again with pre populated data
        else:
            return render(request, 'login.html', {'form': form})
    else:
        form = LoginForm()
        return render(request, 'login.html', {'form': form})


def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, 'successfully logged out')
        return redirect('/')
    else:
        messages.info(request, 'you\re already logged out')
        return redirect('/')
        

class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        user_email = form.cleaned_data['email']

        associated_user = User.objects.filter(Q(email=user_email))
        if not associated_user.exists():
            messages.error(self.request, 'Email not found. please create an acount')
            return redirect(resolve_url('password_reset'))

        return super().form_valid(form)