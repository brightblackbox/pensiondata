from celery import shared_task, current_task

from .models import PlanAnnualAttribute, PlanAttribute, Plan, DataSource


@shared_task
def import_to_database(data, model_name, source='Census', format='txt'):
    """
    :param data: list of lines

    """

    current_task.update_state(
                state='PROGRESS',
                meta={'process_percent': 0, 'imported_count': 0}
    )

    row_counts = len(data)
    if row_counts == 0:
        return True

    cur_row_num = 1
    imported_count = 0
    for row in data:
        # NOTE: temporary code. should be optimized.
        if model_name == 'Plan'.lower():
            if import_census_plan(row):
                imported_count += 1
        elif model_name == 'PlanAnnualAttribute'.lower():
            if import_census_plan_annual(row):
                imported_count += 1
        else:
            return 0

        process_percent = int(100 * float(cur_row_num) / float(row_counts))
        current_task.update_state(
            state='PROGRESS',
            meta={'process_percent': process_percent, 'imported_count': imported_count}
        )
        cur_row_num += 1
    return imported_count


def import_census_plan(record):

    # parsing

    try:
        census_plan_id = record[0:14].strip()
        name = record[15:100].strip()
        display_name = record[100:188].strip()

    except Exception as e:
        # print(e.__dict__)
        return False

    # Plan

    try:
        plan_obj = Plan.objects.get(census_plan_id=census_plan_id)
        if not (plan_obj.name == name and plan_obj.display_name == display_name):
            plan_obj.name = name
            plan_obj.display_name = display_name
            plan_obj.save()

    except Plan.DoesNotExist:
        Plan.objects.create(census_plan_id=census_plan_id, name=name, display_name=display_name)

    except Plan.MultipleObjectsReturned:
        # print("NOTE: --- There exists dulplicated census_plan_id in Plan Table --- ")
        return False

    return True


def import_census_plan_annual(record):

    # parsing

    try:
        datasource = DataSource.objects.get(name__exact='Census')  # NOTE: hardcoded
        census_plan_id = record[0:14].strip()
        line_item_code = record[14:17].strip()
        value = record[17:29].strip()
        year = record[31:33]
        if int(year) > 80:
            year = '19' + year
        else:
            year = '20' + year

    except Exception as e:
        # print(e.__dict__)
        return False

    # PlanAttribute

    try:
        plan_attr = PlanAttribute.objects.get(line_item_code=line_item_code, data_source=datasource)
        if plan_attr.name is None:
            plan_attr.name = line_item_code
            plan_attr.save()

    except PlanAttribute.DoesNotExist:
        plan_attr = PlanAttribute.objects.create(name=line_item_code, line_item_code=line_item_code, data_source=datasource)
    except PlanAttribute.MultipleObjectsReturned:
        # print("NOTE: --- There exists dulplicated (line_item_code, data_source) in PlanAttribute Table --- ")
        return False

    # Plan

    try:
        plan_obj = Plan.objects.get(census_plan_id=census_plan_id)
    except Plan.DoesNotExist:
        plan_obj = Plan.objects.create(census_plan_id=census_plan_id, name='undefined plan name')

    except Plan.MultipleObjectsReturned:
        # print("NOTE: --- There exists dulplicated census_plan_id in Plan Table --- ")
        return False

    # PlanAnnualAttribute

    try:
        plan_annual = PlanAnnualAttribute.objects.get(plan=plan_obj, plan_attribute=plan_attr, year=year)
        if not (plan_annual.attribute_value == value):
            plan_annual.attribute_value = value
            plan_annual.save()

    except PlanAnnualAttribute.DoesNotExist:
        PlanAnnualAttribute.objects.create(plan=plan_obj, plan_attribute=plan_attr, year=year, attribute_value=value)

    except PlanAnnualAttribute.MultipleObjectsReturned:
        # print("NOTE: --- There exists dulplicated (planm plan_attribute, year) in PlanAnnualAttribute Table --- ")
        return False

    return True
