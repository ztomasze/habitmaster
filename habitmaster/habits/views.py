"""
Habits, creation, index overview, and details of a single habit.
"""

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from habitmaster.habits.models import DaysOfWeekSchedule, IntervalSchedule, Habit, Activity
from habitmaster.habits.models import daysInStreak
import datetime

@login_required
def index(request):
    """ Main habit overview page. """
    context = {'user': request.user}
    context['habits'] = Habit.objects.filter(user=request.user)
    context['today'] = datetime.date.today()
    return render(request, 'habits/index.html', context)
    
@login_required
def create(request):
    """
    Create a new habit.
    """
    context = {}
    if request.method == 'POST':
        schedule = False
        if not request.POST['task']:
            context['create_error'] = "You did not enter a description of your Task To Do."
        elif 'schedule' not in request.POST:
            context['create_error'] = ("Did you want your habit to occur on specific days of "
            "the week or on a regular rotating schedule?  Please select the corresponding "
            "radio button.")
        else:
            # big two are fine, so check finer details while creating schedule
            if request.POST['schedule'] == 'days':
                # convert
                days = ''
                for day in DaysOfWeekSchedule.DAYS_OF_WEEK:
                    days += str(1 if day in request.POST else 0)
                #try
                if int(days):  # not all 0s
                    schedule = DaysOfWeekSchedule(days=days)
                else:
                    context['create_error'] = ("You said you wanted your habit to fall on "
                        "certain days, but you did not check the boxes for any specific days.")

            elif request.POST['schedule'] == 'fixed':
                schedule = IntervalSchedule(interval=request.POST['interval'])
            
            else:
                context['create_error'] = ("Bad form submission: Unrecognized schedule type.")

        if schedule:
            try:
                schedule.save()
                habit = Habit(user=request.user, task=request.POST['task'], schedule=schedule)
                # XXX: For now... design suggests that we should start with pending
                habit.active = True
                habit.save()
                return HttpResponseRedirect(reverse('index'))
            except DatabaseError as e:
                context['create_error'] = "Could not save new habit: " + str(e)                            
        
    # either GET request or an error resulted in POST request
    return render(request, 'habits/create.html', context)
    

@login_required
def detail(request, habit_id):
    """
    Display the detailed view for a single habit.
    """
    context = {}
    try:
        habit = Habit.objects.get(id=habit_id)
    except:
        context['error_mesg'] = ("Sorry, but habit #" + str(habit_id) + 
            " was not found in the database.")
        return render(request, 'habits/error.html', context)
    if habit.user != request.user:
        context['error_mesg'] = ("Sorry, but habit #" + str(habit_id) + "is not your habit, "
            "so you do not have permission to view it.")
        return render(request, 'habits/error.html', context)
        
    context['habit'] = habit
    context['status'] = habit.getStarLevel()
    streaks = habit.getStreaks()
  
    longest = max(streaks, key=len)    
    context['longest_times'] = len(longest)
    if longest == streaks[-1]:
        context['longest_days'] = daysInStreak(longest, until=datetime.date.today())
    else:
        context['longest_days'] = daysInStreak(longest)
    context['activities'] = habit.getActivities(missed=True)
    
    return render(request, 'habits/detail.html', context)


@login_required
def activity_create(request):
    context = {}
    if request.method == 'POST':
        try:
            habit = Habit.objects.get(id=request.POST['habit'])
        except:
            context['error_mesg'] = ("Sorry, but either habit id was not given or "
                " was not found in the database.")
            return render(request, 'habits/error.html', context)
        if habit.user != request.user:
            context['error_mesg'] = ("Sorry, but habit #" + str(habit_id) + "is not your habit, "
                "so you do not have permission to view or modify it.")
            return render(request, 'habits/error.html', context)
        
        acts = Activity.objects.filter(habit=habit, date=datetime.date.today())
        if acts:
            context['error_mesg'] = "An activity with today's date already exists: " + str(acts[0])
        else:        
            try:
                act = Activity.objects.create(date=datetime.date.today(), habit=habit)
                act.save()
                return HttpResponseRedirect(reverse('index'))
            except DatabaseError as e:
                context['error_mesg'] = "Could not create new activity: " + str(e)        
    
    else:
        # FIXME: replace with form
        context['error_mesg'] = "Not a POST request."
        
    if 'error_mesg' in context:
        return render(request, 'habits/error.html', context)
    
    return render(request, 'habits/index.html', context)
