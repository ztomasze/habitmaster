"""
User pages, such as creating a new user and logging in.
"""

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
import django.contrib.auth
from django.contrib.auth.models import User

def create(request):
    context = {}
    try:
        if not request.POST['password']:
            context['create_error'] = "You must provide a password."  #email "optional"
        elif request.POST['password'] != request.POST['password_again']:
            context['create_error'] = "Your retyped password did not match the original."
        else:
            user = User.objects.create_user(request.POST['username'], 
                                            request.POST['email'], 
                                            request.POST['password'])
            return login(request)
    except ValueError:
        context['create_error'] = "Invalid username."
    except KeyError:
        context['create_error'] = "Your request was missing some required fields."
            
    return render(request, 'users/login.html', context)

    
def login(request):
    context = {}
    try:
        user = django.contrib.auth.authenticate(username=request.POST['username'], 
                                                password=request.POST['password'])
        if user is not None:
            # the password verified for the user
            if user.is_active:
                # login and then send back to main page (if didn't request other page)
                django.contrib.auth.login(request, user)                
                if 'next' in request.GET:
                    return HttpResponseRedirect(request.GET['next'])
                else:
                    return HttpResponseRedirect(reverse('index'))
            else:
                context['login_error'] = "Your account has been disabled."
        else:
            context['login_error'] = "Username or password given was incorrect."
    except KeyError:
        pass  # no username or password, so let fall through

    return render(request, 'users/login.html', context)

def logout(request):
    django.contrib.auth.logout(request)
    return HttpResponseRedirect(reverse('login'))
    
    