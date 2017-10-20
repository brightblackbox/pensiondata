# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-19 19:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('moderation', '0003_rename_fields_to_be_shorter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='moderatedobject',
            name='by',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='moderated_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='moderatedobject',
            name='state',
            field=models.SmallIntegerField(choices=[(0, 'Ready for moderation'), (1, 'Draft'), (2, 'Add'), (3, 'Delete')], default=1, editable=False),
        ),
        migrations.AlterField(
            model_name='moderatedobject',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Rejected'), (1, 'Approved'), (2, 'Pending')], default=2, editable=False),
        ),
    ]
