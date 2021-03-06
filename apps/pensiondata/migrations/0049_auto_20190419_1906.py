# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-04-19 19:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pensiondata', '0048_sproc_master_attribute'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanAnnualAttributesMaster',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('year', models.CharField(max_length=4)),
                ('plan_attribute_id', models.BigIntegerField()),
                ('plan_attribute_name', models.CharField(blank=True, max_length=255, null=True)),
                ('plan_attribute_multiplier', models.DecimalField(blank=True, decimal_places=6, default=1000, max_digits=30, null=True)),
                ('plan_attribute_datatype', models.CharField(blank=True, max_length=256, null=True)),
                ('attribute_category_id', models.BigIntegerField()),
                ('attribute_category_name', models.CharField(max_length=255, unique=True)),
                ('data_source_id', models.BigIntegerField()),
                ('data_source_name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'managed': False,
            },
        ),
        migrations.AddField(
            model_name='planannualmasterattribute',
            name='master_attribute',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='pensiondata.PlanMasterAttributeNames'),
        ),
        migrations.AlterField(
            model_name='planannualmasterattribute',
            name='plan_attribute',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='pensiondata.PlanAttribute'),
        ),
        migrations.AlterField(
            model_name='planattributemaster',
            name='master_attribute',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='attr_master', to='pensiondata.PlanMasterAttributeNames'),
        ),
    ]
