"""
Tests habit-related classes.  Use "manage.py test" to run.
"""

from django.test import TestCase
from habitmaster.habits.models import DaysOfWeekSchedule, IntervalSchedule
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
        
