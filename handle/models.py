from __future__ import unicode_literals
from django.core.validators import MaxValueValidator
from django.db import models

# Create your models here.
class Customer(models.Model):
	phone_number = models.CharField(primary_key=True, max_length=10)
	first_name = models.CharField(max_length=80)
	last_name = models.CharField(max_length=80)
	pin = models.CharField(max_length=4)
	capital_one_id = models.CharField(max_length=80, blank=True, null=True)
	def __repr__(self):
		return "%s %s - %s" % (self.first_name, self.last_name, self.phone_number)

class outstanding_requests(models.Model):
	issuer = models.ForeignKey(Customer, related_name="request_issuer")
	debtor = models.ForeignKey(Customer, related_name="request_debtor")
	amount = models.DecimalField(decimal_places=2, max_digits=9)
	def __repr__(self):
		return "$%s owed by %s to %s" % (self.amount, self.debtor.first_name + " " + self.debtor.last_name, self.issuer.first_name + " " + self.issuer.last_name)
	def show(self):
		return "$%s - %s %s" % (self.amount, self.issuer.first_name, self.issuer.last_name)