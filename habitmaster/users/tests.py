"""
Tests habitmaster.users.  These will pass when you run "manage.py test".
"""

from django.test import TestCase
from django.db import IntegrityError
from django.core.validators import ValidationError
from habitmaster.users.models import User

class UserTest(TestCase):

    def setUp(self):
        self.valid = User.objects.create(email="user@test.com", password="fish")

    def test_creation(self):
        with self.assertRaises(ValidationError):
            obj = User.objects.create(email="not an email address", password="turtle")
            obj.clean_fields()
        with self.assertRaises(IntegrityError):
            User.objects.create(email="user@test.com", password="duplicateAccount")
