# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-07 19:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pensiondata', '0004_auto_20171007_1917'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='planinheritance',
            options={'managed': False},
        ),
        migrations.AlterModelOptions(
            name='planprovisions',
            options={'managed': False},
        ),
        # migrations.AlterUniqueTogether(
        #     name='planannualattribute',
        #     unique_together=set([('plan', 'year', 'plan_attribute')]),
        # ),
    ]
