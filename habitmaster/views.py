"""
Top-level pages, such as main page.
"""

from django.shortcuts import render

def index(request):
    """ Main page. """
    context = {}
    return render(request, 'index.html', context)

    