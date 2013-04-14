from django.db import models

class User(models.Model):
    """ A HabitMaster user account. """
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=50)  # XXX: should be storing hashes or something!

    