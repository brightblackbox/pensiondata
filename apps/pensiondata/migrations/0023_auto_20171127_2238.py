# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-11-27 22:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pensiondata', '0022_auto_20171127_2101'),
    ]

    operations = [

        migrations.AlterField(
            model_name='planannualattribute',
            name='attribute_value',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),

        migrations.AlterUniqueTogether(
            name='planannualattribute',
            unique_together=set([('plan', 'year', 'plan_attribute')]),
        ),
    ]
