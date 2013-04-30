"""
Habits, creation, index overview, and details of a single habit.
"""

from django.shortcuts import render
#from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    """ Main habit overview page. """
    context = {'request': request}
    return render(request, 'habits/index.html', context)
    
@login_required
def create(request):
    """
    Create a new habit.
    """
    context = {}
    return render(request, 'habits/create.html', context)
    
