# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-02-19 15:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pensiondata', '0030_auto_20180219_1425'),
    ]

    operations = [
        migrations.AddField(
            model_name='planattribute',
            name='status_calculated',
            field=models.CharField(blank=True, choices=[('in progress', 'in progress'), ('done', 'done')], max_length=255, null=True),
        ),
    ]