from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MaxValueValidator, MinValueValidator
import datetime

# useful streak-processing functions
    
def daysInStreak(streak, until=None):
    """ 
    Returns the number of days covered by the activities recorded in this streak.  
    This is a min of 1 day, unless the streak is empty.
    
    If until is None, looks only at the streak data itself.  If until is set, uses that
    as today's date.
    """
    if not streak:
        return 0
    if until:
        return (until - streak[0].date).days + 1
    else:
        return (streak[-1].date - streak[0].date).days + 1


class Schedule(models.Model):
    
    """
    The superclass of all Schedules, this class provides a number of useful methods to be
    inherited. Some of the methods are "abstract" and are described here so that subclasses
    know what they must override.
    
    For all methods, a streak is a list of activities that form a valid streak for this
    schedule.  Thus, a list of streaks is a list of lists of activities.  See getStreaks
    method for more.
    """
    def __unicode__(self):
        return self.cast().__unicode__()
    
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

    def nextRequiredDay(self, streak, today=None):
        """ 
        Given a streak of activities, what is the date of the next required activity?
        A streak is required because for some schedules, the first activity determines the
        required cycle.  There may be extra activities on non-required days.  Some schedules
        may also need to know what today is.  For example an empty interval streak should
        start today!  (Though if not, tomorrow will work too.)  Also, if today falls on a 
        DaysOfWeekSchedule, whether or not it is required will depend on whether it is
        already the last day in the streak.
        
        ABSTRACT: Must be overridden. Currently returns None.
        """
        return None
    
    def cast(self):
        """
        Because schedule is abstract and connected by a foreign key, you may occasionally
        get a Schedule back in practice, rather than the specific subclass.  This method
        will get you the specific instance.  Use this before calling any of the ABSTRACT
        Schedule methods on on a Schedule object.
        """
        # XXX: Just listed the subtypes explicitly rather than using scalable reflection
        inst = None
        if not inst:
            try:
                inst = IntervalSchedule.objects.get(schedule_ptr_id=self.id)
            except IntervalSchedule.DoesNotExist:
                pass
        if not inst:
            try:
                inst = DaysOfWeekSchedule.objects.get(schedule_ptr_id=self.id)
            except DaysOfWeekSchedule.DoesNotExist:
                pass
        return inst
        
        
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
                if today > req or not streaks:
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
            
    def nextRequiredDay(self, streak, today=None):
        if not today:
            today = datetime.date.today()
        # regardless of current streak state, next day is the same according to schedule
        reqDays = self.iterFromDate(today)
        return reqDays.next()
        
        
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
#FIXME        
    def nextRequiredDay(self, streak, today=None):
        """ Any day will work as a valid start day of a new streak. """
        if not today:
            today = datetime.date.today()
        if not streak:
            return today
        print streak
        span = streak[-1].date - streak[0].date
        print "Span:", span.days
        extraDays = span.days % self.interval
        print "Extra:", extraDays
        tilReq = self.interval - extraDays
        return streak[-1].date + datetime.timedelta(days=tilReq)
        
        
class Habit(models.Model):
    """ 
    The habit to establish, which consists of a task repeated on the given schedule. 
    """
    
    # the possible "stars" level of a habit
    STAR_LEVELS = ("Pending", "Bronze", "Silver", "Gold")
    
    user = models.ForeignKey(User)
    task = models.CharField(max_length=200)
    schedule = models.ForeignKey(Schedule)
    created = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.task

    def getActivities(self, missed=False):
        activities = Activity.objects.filter(habit=self)
        if not missed:
            activities = activities.exclude(status=Activity.MISSED)
        return activities.order_by('date')
    
    def getCurrentStreakDays(self, today=None):
        """ Returns the number of days in the most recent streak, from first activity until today. """
        streaks = self.getStreaks(today);
        if not streaks:
            return 0
        if not today:
            today=datetime.date.today()
        return daysInStreak(streaks[-1], until=today)  

    def getCurrentStreakTimes(self, today=None):
        """ Returns the number of activities in the most recent streak. """
        streaks = self.getStreaks(today);
        if not streaks:
            return 0
        return len(streaks[-1])        

    def getStarLevel(self, today=None):
        """ 
        Returns the appropriate value from STAR_LEVELS for this habit. 
        Can override what today's date is
        """
        if not today:
            today = datetime.date.today()
        
        if not self.active:
            return Habit.STAR_LEVELS[0]
        streaks = self.schedule.getStreaks(self.getActivities(), today);
        if not streaks:
            return Habit.STAR_LEVELS[1]
        
        # consider most recent streak, but also the one before that
        recentDays = daysInStreak(streaks[-1], until=today)
        pastDays = 0
        if len(streaks) > 1:
            pastDays = daysInStreak(streaks[-2], until=None)

        if recentDays > 28:
            return Habit.STAR_LEVELS[3]  # gold
        elif recentDays > 14:
            if pastDays > 28:
                return Habit.STAR_LEVELS[3]  # returned to gold from silver
            else:
                return Habit.STAR_LEVELS[2]  # just silver
        else:
            if pastDays > 28:
                return Habit.STAR_LEVELS[2]  # silver because of recent gold lapse
            else:
                return Habit.STAR_LEVELS[1]  # bronze
    
    def getStartDate(self):
        """ 
        Returns the date of the first activity for this habit, else None. 
        The date is returned regardless of whether the habit is active or not.
        """
        streaks = self.getStreaks()
        if streaks[0]:
            return streaks[0][0].date
        return None
    
    def getStreaks(self, today=None):
        # streak computation is the most intensive thing we do, so lets just do it once
        if not hasattr(self, 'streaks') or today != self.streaks_date:
            sched = self.schedule.cast()
            self.streaks = sched.getStreaks(self.getActivities(), today)
            self.streaks_date = today
        return self.streaks
                         
    def getTotalTimes(self):
        """ Returns the number of completed activities for this habit. """
        return self.getActivities().count()
        
    def getTotalDays(self, today=None):
        if not today:
            today = datetime.date.today()
        activities = self.getActivities()
        if not activities:
            return 0
        return (today - self.getActivities()[0].date).days
    
  

  
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
    