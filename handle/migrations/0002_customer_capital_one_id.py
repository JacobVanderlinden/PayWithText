# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-10-23 09:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('handle', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='capital_one_id',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
    ]
