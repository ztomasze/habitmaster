from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# All habitmaster URLs are current here, rather than divided up into app-specific sets.

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'habitmaster.views.home', name='home'),
    # url(r'^habitmaster/', include('habitmaster.foo.urls')),
    url(r'^$', 'habitmaster.habits.views.index', name='index'),

    url(r'^habit/new/$', 'habitmaster.habits.views.create', name='habits_create'),
    url(r'^habit/(?P<habit_id>\d+)/$', 'habitmaster.habits.views.detail', name='habit'),
    
    url(r'^create/$', 'habitmaster.users.views.create', name='create'),
    url(r'^login/$', 'habitmaster.users.views.login', name='login'),
    url(r'^logout/$', 'habitmaster.users.views.logout', name='logout'),
    
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
