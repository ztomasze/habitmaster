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

    def test_iterFromDate(self):
        i = self.weekend.iterFromDate(datetime.date(2013, 5, 2))
        self.assertEqual(i.next(), datetime.date(2013, 5, 4))
        self.assertEqual(i.next(), datetime.date(2013, 5, 5))
        self.assertEqual(i.next(), datetime.date(2013, 5, 11))
        i = self.weekend.iterFromDate(datetime.date(2013, 5, 5))
        self.assertEqual(i.next(), datetime.date(2013, 5, 5))
        i = self.weekdays.iterFromDate(datetime.date(2013, 5, 4))
        self.assertEqual(i.next(), datetime.date(2013, 5, 6))
        i = self.weekdays.iterFromDate(datetime.date(2013, 5, 3))
        self.assertEqual(i.next(), datetime.date(2013, 5, 3))
        self.assertEqual(i.next(), datetime.date(2013, 5, 6))
        self.assertEqual(i.next(), datetime.date(2013, 5, 7))
        
        
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
        self.weekdays = DaysOfWeekSchedule.objects.create(days='1111100')
        self.every2 = IntervalSchedule.objects.create(interval=2)
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

    def test_getStreaks_Interval(self):
        activities = Activity.objects.all().order_by('date')

        streaks = self.every3.getStreaks(activities, today=datetime.date(2013, 5, 25))
        self.assertEqual(5, len(streaks))
        self.assertEqual(streaks[-1][-1].date, datetime.date(2013, 5, 24))

        streaks = self.every2.getStreaks(activities, today=datetime.date(2013, 5, 26))
        self.assertEqual(3, len(streaks))
        self.assertEqual(streaks[-1][-1].date, datetime.date(2013, 5, 24))
        
        # check appended current streak 
        streaks = self.every2.getStreaks(activities, today=datetime.date(2013, 5, 27))
        self.assertEqual(4, len(streaks))
        self.assertEqual([], streaks[-1])

        streaks = self.every3.getStreaks([])
        self.assertEqual(1, len(streaks))
        self.assertEqual([], streaks[-1])

    def test_getStreaks_DaysOfWeek(self):
        activities = Activity.objects.all().order_by('date')
        streaks = self.mwf.getStreaks(activities, today=datetime.date(2013, 5, 27))
        self.assertEqual(2, len(streaks))
        self.assertTrue(streaks[-1])  #non empty list
        
        # test appened current streak
        streaks = self.mwf.getStreaks(activities, today=datetime.date(2013, 5, 28))
        self.assertEqual(3, len(streaks))
        self.assertEqual([], streaks[-1])

        streaks = self.mwf.getStreaks([])
        self.assertEqual(1, len(streaks))
        self.assertEqual([], streaks[-1])

        streaks = self.weekdays.getStreaks(activities, today=datetime.date(2013, 5, 27))
        self.assertEqual(7, len(streaks))
        self.assertTrue(streaks[-1])  #non empty list
        