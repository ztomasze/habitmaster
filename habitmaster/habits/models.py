from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MaxValueValidator, MinValueValidator
import datetime

# useful streak-processing functions
    
def daysInStreak(self, streak, toToday=False):
    """ 
    Returns the number of days covered by the activities recorded in this streak.  
    This is a min of 1 day, unless the streak is empty.
    
    If toToday, this is the number of days from the date of the first activity to today.
    """
    if not streak:
        return 0
    if toToday:
        return (datetime.date.today() - streak[0].date).days + 1
    else:
        return (streak[-1].date - streak[0]).days + 1


class Schedule(models.Model):
    
    """
    The superclass of all Schedules, this class provides a number of useful methods to be
    inherited. Some of the methods are "abstract" and are described here so that subclasses
    know what they must override.
    
    For all methods, a streak is a list of activities that form a valid streak for this
    schedule.  Thus, a list of streaks is a list of lists of activities.  See getStreaks
    method for more.
    """    
    def getStreaks(self, activities, today=None):
        """ 
        Given a flat list of activities, returns a list of lists of those activities where
        each sublist is a streak according to this particular schedule.  Activities should
        be in sorted older-to-newer order.  The given date is used as "today" to determine
        whether the last streak is still ongoing or not.  (If not given, uses today's date.)
        
        Returned list of streaks always includes the current streak as the last entry, 
        even if that streak is empty of any actual activities.
        
        ABSTRACT: Must be overridden. Currently returns an empty list (no streaks at all).  
        """
        return []

    def nextRequired(self, date, floor=True):
        """ 
        Given a date, what is the date of the next required activity?
        If floor=True, will return the soonest possible date, even if that is the
        date given.  Otherwise, finds the first requirement after the given date.
        
        ABSTRACT: Must be overridden. Currently returns None.
        """
        return None
    
        
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
        

    def iterFromDate(self, date):
        """
        Returns a generator (iterator) that returns a continuing series of date
        objects that correspond to this schedule.  The first date returned will be the
        given date if it falls on one of the days of this schedule, otherwise it will
        the first date after that.
        """
        class DateIter(object):
            
            def __init__(self, days, startDate):
                self.schedule = days

                # advance to first valid day
                offset = 0
                while self.schedule[(startDate.weekday() + offset) % 7] == '0':
                    offset += 1
                self.day = startDate + datetime.timedelta(offset)

            def __iter__(self):
                return self
                
            def next(self):
                current = self.day
                offset = 1
                while self.schedule[(self.day.weekday() + offset) % 7] == '0':
                    offset += 1
                self.day += datetime.timedelta(offset)
                return current

        return DateIter(self.days, date)
    
    def getStreaks(self, activities, today=None):
        if not activities:
            return [[]]  # on current empty streak
        if not today:
            today = datetime.date.today()
        
        streaks = []
        streak = []
        reqDays = self.iterFromDate(activities[0].date)
        i = 0 
        for req in reqDays:  # infinite loop
            # usually 0 or 1, but any mismatches before a req
            while i < len(activities) and activities[i].date < req:
                streak.append(activities[i])
                i += 1
                streaks.append(streak)  # each mismatch produces a new broken streak
                streak = []
                
            if i == len(activities):
                # all activities processed... 
                if streak:
                    streaks.append(streak)
                # but see if we're still valid
                if today > req:
                    streaks.append([])  # now on an empty current streak
                break
                
            if activities[i].date > req:
                # missed a req day
                if streak:
                    streaks.append(streak)
                    streak = []
            else:
                assert activities[i].date == req
                streak.append(activities[i])
                i += 1                  
                
        return streaks
            
        
class IntervalSchedule(Schedule):
    """
    The habit must be exercised at least once every X days, where X is 1 to 7.
    """
    interval = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)])

    def __unicode__(self):
        return 'Once every ' + str(self.interval) + ' days'

        
    def getStreaks(self, activities, today=None):
        if not activities:
            return [[]]  # on current empty streak
        if not today:
            today = datetime.date.today()
            
        streaks = []
        streak = []
        startDate = None
        for act in activities:
            if not startDate:
                # starting a new streak
                startDate = act.date
                streak.append(act)
            else:
                if (act.date - startDate).days % self.interval == 0:
                    # on the correct day
                    streak.append(act)
                else:
                    if (act.date - startDate).days > self.interval:
                        # current streak lapsed and this is start of a new one
                        streaks.append(streak)
                        streak = [act]
                        startDate = act.date
                    else:
                        # wrong date, but might yet be another on the required day
                        streak.append(act)

        streaks.append(streak)  #add last streak (may be empty)
        
        # see if most recent streak is still an active one
        if streaks[-1]:
            lastAct = streaks[-1][-1]
            if (today - lastAct.date).days > self.interval:
                # streak lapsed
                streaks.append([])  # now on an empty current streak
        
        return streaks
        

        
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
    
    def getDate(self):
        """Returns an ISO-formatted date."""
        return self.date.isoformat()
    
    def __unicode__(self):
        return self.getDate() + ": " + self.habit.task
    