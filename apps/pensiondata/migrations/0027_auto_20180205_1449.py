# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-02-05 14:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pensiondata', '0026_auto_20180129_1416'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasource',
            name='private',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='governmentattribute',
            name='datatype',
            field=models.CharField(blank=True, choices=[('text', 'text'), ('yesno', 'yesno'), ('percentage', 'percentage'), ('percentage2', 'percentage2'), ('int', 'int'), ('percentage4', 'percentage4'), ('real', 'real')], max_length=256, null=True),
        ),
    ]