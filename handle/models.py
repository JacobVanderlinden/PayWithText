from __future__ import unicode_literals
from django.core.validators import MaxValueValidator
from django.db import models

# Create your models here.
class Customer(models.Model):
	phone_number = models.CharField(primary_key=True, max_length=10)
	first_name = models.CharField(max_length=80)
	last_name = models.CharField(max_length=80)
	pin = models.IntegerField()
	capital_one_id = models.CharField(max_length=80, blank=True, null=True)
	def __repr__(self):
		return "%s %s - %s" % (self.first_name, self.last_name, self.phone_number)