"""
Tests habit-related classes.  Use "manage.py test" to run.
"""
import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from habitmaster.habits.models import DaysOfWeekSchedule, IntervalSchedule, Habit, Activity
from django.core.validators import ValidationError

class DaysOfWeekScheduleTest(TestCase):
    
    def setUp(self):
        self.weekdays = DaysOfWeekSchedule.objects.create(days='1111100')
        self.weekend = DaysOfWeekSchedule.objects.create(days='0000011')

    def test_badSetUp(self):
        with self.assertRaises(ValidationError):
            obj = DaysOfWeekSchedule.objects.create(days='1111')
            obj.clean_fields()
        with self.assertRaises(ValidationError):
            obj = DaysOfWeekSchedule.objects.create(days='1234567')
            obj.clean_fields()
        
    def test_asNames(self):
        self.assertEqual(self.weekdays.asNames(), ['Mo', 'Tu', 'We', 'Th', 'Fr'])
        self.assertEqual(self.weekend.asNames(), ['Sa', 'Su'])
        
    def test_unicode(self):
        self.assertEqual(self.weekdays.__unicode__(), 'Mo/Tu/We/Th/Fr')
        self.assertEqual(self.weekend.__unicode__(), 'Sa/Su')


class IntervalScheduleTest(TestCase):
    def setUp(self):
        self.every3 = IntervalSchedule.objects.create(interval=3)

    def test_badSetUp(self):
        with self.assertRaises(ValidationError):
            obj = IntervalSchedule.objects.create(interval=0)
            obj.clean_fields()
        with self.assertRaises(ValidationError):
            obj = IntervalSchedule.objects.create(interval=8)
            obj.clean_fields()    

    def test_unicode(self):
        self.assertEqual(self.every3.__unicode__(), 'Once every 3 days')
        
class HabitTest(TestCase):
    def setUp(self):
        self.mwf = DaysOfWeekSchedule.objects.create(days='1010100')
        self.every3 = IntervalSchedule.objects.create(interval=3)
        user = User.objects.create_user('tester')
        self.habitDays = Habit.objects.create(user=user, task='Work it', schedule=self.mwf)
        self.habitInterval = Habit.objects.create(user=user, task='Test it', schedule=self.every3)
        
        Activity.objects.create(habit=self.habitDays, date=datetime.date(2013, 5, 8))
        Activity.objects.create(habit=self.habitDays, date=datetime.date(2013, 5, 6))
        Activity.objects.create(habit=self.habitDays, date=datetime.date(2013, 5, 10))
        Activity.objects.create(habit=self.habitDays, date=datetime.date(2013, 5, 15))
        Activity.objects.create(habit=self.habitDays, date=datetime.date(2013, 5, 17))
        Activity.objects.create(habit=self.habitDays, date=datetime.date(2013, 5, 20))
        Activity.objects.create(habit=self.habitDays, date=datetime.date(2013, 5, 24))
        Activity.objects.create(habit=self.habitDays, date=datetime.date(2013, 5, 22))
        
    def test_getTotalTimes(self):
        self.assertEqual(8, self.habitDays.getTotalTimes())
        
    def test_getTotalDays(self):
        self.assertEqual((datetime.date.today() - datetime.date(2013, 5, 6)).days, 
                         self.habitDays.getTotalDays())    