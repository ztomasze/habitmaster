"""
User pages, such as creating a new user and logging in.
"""

from django.shortcuts import render

def create(request):
    """ Main page. """
    context = {}
    return render(request, 'users/create.html', context)
