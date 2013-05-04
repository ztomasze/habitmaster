from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MaxValueValidator, MinValueValidator
import datetime

# useful streak-processing functions
    
def daysInStreak(self, streak, isCurrent=False):
    """ 
    Returns the number of days covered by the activities in this streak.  
    If isCurrent, this is the number of days from the first activity to today.
    """
    pass



class Schedule(models.Model):
    
    """
    The superclass of all Schedules, this class provides a number of useful methods to be
    inherited. Some of the methods are "abstract" and are described here so that subclasses
    know what they must override.
    
    For all methods, a streak is a list of activities that form a valid streak for this
    schedule.  Thus, a list of streaks is a list of lists of activities.  See getStreaks
    method for more.
    """    
    def getStreaks(self, activities):
        """ 
        Given a flat list of activities, returns a list of lists of those activities where
        each sublist is a streak according to this particular schedule.  Activities should
        be in sorted older-to-newer order.
        
        Returned list of streaks always includes the current streak as the last entry, 
        even if that streak is empty of any actual activities.
        
        ABSTRACT: Currently returns an empty list (no streaks at all).  Must be overridden.
        """
        return []

    
        
class DaysOfWeekSchedule(Schedule):
    """
    Represents which specific days of the week the habit should be exercised.
    Days are given in Mon-Sun order, with 1 or 0 indicating each day.
    """
    DAYS_OF_WEEK = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
    
    days = models.CharField(max_length=7, 
            validators=[RegexValidator(r'[01]{7}', "Value must be seven 0s or 1s")])

    def asNames(self):
        """ 
        Returns the required days of this schedule as a list of 2-char method names. 
        """
        names = []
        for (i, day) in enumerate(self.days):
            if (day == '1'):
                names.append(self.DAYS_OF_WEEK[i])
        return names
    
    def __unicode__(self):
        return "/".join(self.asNames())
        
    def nextRequired(self, date, floor=True):
        """ 
        Given a date, what is the date of the next required activity?
        If floor=True, will return the soonest possible date, even if that is the
        date given.  Otherwise, finds the first requirement after the given date.
        """
        pass
#TODO    
        
    def getStreaks(self, activities):
        streaks = []
        streak = []
#TODO:        for act in activities:
        return streaks
        
        
        
class IntervalSchedule(Schedule):
    """
    The habit must be exercised at least once every X days, where X is 1 to 7.
    """
    interval = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)])

    def __unicode__(self):
        return 'Once every ' + str(self.interval) + ' days'


        
class Habit(models.Model):
    """ 
    The habit to establish, which consists of a task repeated on the given schedule. 
    """
    user = models.ForeignKey(User)
    task = models.CharField(max_length=200)
    schedule = models.ForeignKey(Schedule)
    created = models.DateField(auto_now_add=True)
    
    def getActivities(self, missed=False):
        return Activity.objects.filter(habit=self).order_by('date')
    
    def getTotalTimes(self):
        """ Returns the number of completed activities for this habit. """
        activities = self.getActivities().exclude(status=Activity.MISSED)
        return activities.count()
        
    def getTotalDays(self):
        return (datetime.date.today() - self.getActivities()[0].date).days
    
    def __unicode__(self):
        return self.task
  

  
# The name of this class was something of challenge.  Names considered:
# * Doing, DidIt, Done, Effort, Action, Push
# * Event, Activity, Task, 
# * Checkmark, Record, Day, Session
# * Application, Execution, Performance, Practice, Step, Success, Fulfillment
# * Realization, Instance
#
class Activity(models.Model):
    """ An application of a habit on a particular day. """
    MISSED = 0
    COMPLETED = 10
    HALF = 5
    WHOLE = 15
    
    STATUS_LEVELS = (
        (MISSED, 'Missed'),
        (COMPLETED, 'Completed'),
        (HALF, 'Half-Hearted'),
        (WHOLE, 'Whole-Hearted'),    
    )
    
    habit = models.ForeignKey(Habit)    
    date = models.DateField()
    status = models.IntegerField(choices=STATUS_LEVELS, default=COMPLETED)
    note = models.TextField(blank=True)
    
    