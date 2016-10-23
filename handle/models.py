from __future__ import unicode_literals
from django.core.validators import MaxValueValidator
from django.db import models

# Create your models here.
class Customer(models.Model):
	phone_number = models.CharField(primary_key=True, max_length=10)
	first_name = models.CharField(max_length=80)
	last_name = models.CharField(max_length=80)
	pin = models.IntegerField()
	def __repr__(self):
		return str(self.phone_number)