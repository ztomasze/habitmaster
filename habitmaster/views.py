"""
Top-level pages, such as user login.
"""

from django.shortcuts import render

def index(request):
    """ Main page. """
    context = {}
    return render(request, 'index.html', context)

    