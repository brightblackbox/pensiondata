# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-02-19 14:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pensiondata', '0029_auto_20180216_1047'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='generatecalculatedattributedata',
            options={'verbose_name': 'Calculated Attribute'},
        ),
        migrations.AlterField(
            model_name='governmentattribute',
            name='datatype',
            field=models.CharField(blank=True, choices=[('int', 'int'), ('int_separated3', 'int_separated3'), ('percentage', 'percentage'), ('percentage2', 'percentage2'), ('percentage4', 'percentage4'), ('real', 'real'), ('shortdate', 'shortdate'), ('text', 'text'), ('yesno', 'yesno')], max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='planattribute',
            name='datatype',
            field=models.CharField(blank=True, choices=[('int', 'int'), ('int_separated3', 'int_separated3'), ('percentage', 'percentage'), ('percentage2', 'percentage2'), ('percentage4', 'percentage4'), ('real', 'real'), ('shortdate', 'shortdate'), ('text', 'text'), ('yesno', 'yesno')], max_length=256, null=True),
        ),
    ]
