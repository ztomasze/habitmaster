"""
Top-level pages, such as main page.
"""

from django.shortcuts import render
#from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    """ Main page. """
    context = {'request': request}
    return render(request, 'index.html', context)

    