from django.db import models
from django.core.validators import RegexValidator, MaxValueValidator, MinValueValidator
from habitmaster.users.models import User


class Schedule(models.Model):
    pass

    
class DaysOfWeekSchedule(Schedule):
    """
    Represents which specific days of the week the habit should be exercised.
    Days are given in Mon-Sun order, with 1 or 0 indicating each day.
    """
    DAYS_OF_WEEK = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
    
    days = models.CharField(max_length=7, validators=[RegexValidator(r'[01]{7}', "Value must be seven 0s or 1s")])

    def asNames(self):
        """ Returns the required days of this schedule as a list of 2-char method names. """
        names = []
        for (i, day) in enumerate(self.days):
            if (day == '1'):
                names.append(self.DAYS_OF_WEEK[i])
        return names
    
    def __unicode__(self):
        return "/".join(self.asNames())
        
    
class InterervalSchedule(Schedule):
    """
    The habit must be exercised at least once every X days, where X is 1 to 7.
    """
    interval = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)])

    def __unicode__(self):
        return 'Once every ' + self.interval + ' days'
        

        
class Habit(models.Model):
    """ The habit to establish, which consists of a task repeated on the given schedule. """
    user = models.ForeignKey(User)
    task = models.CharField(max_length=200)
    schedule = models.ForeignKey(Schedule)
    
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
    status = models.IntegerField(choices=STATUS_LEVELS)
    note = models.TextField()
    
    