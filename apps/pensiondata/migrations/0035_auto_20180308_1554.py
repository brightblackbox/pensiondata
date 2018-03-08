# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-03-08 15:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pensiondata', '0034_auto_20180308_1341'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='planbenefitdesign',
            name='date',
        ),
        migrations.AlterField(
            model_name='planbenefitdesign',
            name='hired_before_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='planbenefitdesign',
            name='hired_on_or_after_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]