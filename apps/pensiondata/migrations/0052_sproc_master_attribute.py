# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2019-04-01 23:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    sql = """
        create or replace function update_plan_annual_master_attribute()
          returns void
        as $$
        begin
          truncate table plan_annual_master_attribute;
 
          drop table if exists temp_annual_attribute;
 
          drop table if exists temp_top_priorities;
 
          create temporary table temp_annual_attribute as
            select
              plan_annual_attribute.plan_id,
              plan_annual_attribute.plan_attribute_id,
              plan_attribute_master.master_attribute_id,
              plan_annual_attribute.year,
              plan_annual_attribute.attribute_value,
              plan_attribute.multiplier,
              plan_attribute_master.priority
            from plan_annual_attribute
              inner join plan_attribute_master
                on (plan_annual_attribute.plan_attribute_id = plan_attribute_master.plan_attribute_id)
                  inner join plan_attribute
                    on (plan_annual_attribute.plan_attribute_id = plan_attribute.id);
                                                               
          update temp_annual_attribute
            set attribute_value = CAST(REGEXP_REPLACE(COALESCE(attribute_value,'0'), '[^0-9]+', '', 'g') AS decimal(21,6)) * multiplier
            where multiplier is not null and multiplier <> 1 and attribute_value <> '' and attribute_value is not null;

          create temporary table temp_top_priorities as
            select
              plan_id,
              master_attribute_id,
              year,
              min(priority) as top_priority
            from temp_annual_attribute
            group by plan_id, master_attribute_id, year;
 
          insert into plan_annual_master_attribute (year, attribute_value, plan_id, plan_attribute_id, master_attribute_id)
            select
              temp_annual_attribute.year,
              temp_annual_attribute.attribute_value,
              temp_annual_attribute.plan_id,
              temp_annual_attribute.plan_attribute_id,
              temp_annual_attribute.master_attribute_id
            from temp_annual_attribute
              inner join temp_top_priorities on
                                               (temp_annual_attribute.plan_id = temp_top_priorities.plan_id and
                                                temp_annual_attribute.year = temp_top_priorities.year and
                                                temp_annual_attribute.master_attribute_id = temp_top_priorities.master_attribute_id and
                                                temp_annual_attribute.priority = temp_top_priorities.top_priority);
        end;  $$
        language 'plpgsql';
    """

    reverse_sql = "drop function update_plan_annual_master_attribute()"

    dependencies = [
        ('pensiondata', '0051_auto_20190419_2211'),
    ]

    operations = [
        migrations.RunSQL(sql, reverse_sql)
    ]
