# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-03-16 07:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pensiondata', '0041_auto_20180315_0827'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='planbenefitdesign',
            options={'verbose_name': 'Plan Benefit Design'},
        ),
        migrations.AlterModelOptions(
            name='planinheritance',
            options={'managed': False, 'verbose_name_plural': 'Plan Inheritance'},
        ),
    ]
