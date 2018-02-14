import re
from celery import shared_task, current_task, task

from .models import PlanAnnualAttribute, PlanAttribute, Plan, DataSource


def parse_calculate_rule_string(qs, attribute_value=False):
    calculated_rule = qs.calculated_rule
    calculated_rule = re.sub('[#]', '', calculated_rule)
    parsed_list = re.findall(r"\%\d+\%|\d+|[\s+-/*]", calculated_rule)

    list_data = []
    list_index_queryset = []

    for item in parsed_list:
        if item.isdigit():
            if not attribute_value:
                plan_annual_attribute = PlanAnnualAttribute.objects.filter(plan_attribute_id=int(item))
            else:
                plan_annual_attribute = PlanAnnualAttribute.objects.filter(
                    plan_attribute_id=int(item), attribute_value=None)
            list_data.append(plan_annual_attribute)
            list_index_queryset.append(parsed_list.index(item))
        else:
            list_data.append(item)

    list_all_parsed_digits = []
    for it in parsed_list:
        for letter in it:
            if any(char.isdigit() for char in letter):
                list_all_parsed_digits.append(it)
    list_all_parsed_digits = list(set(list_all_parsed_digits))

    return list_data, list_index_queryset, parsed_list, list_all_parsed_digits


def get_result_string(parsed_list, list_index_queryset, dict_data, plan, year, qs):
    result_string = ""
    for t in parsed_list:
        if parsed_list.index(t) in list_index_queryset:
            attribute_value = dict_data.get(parsed_list.index(t)).get("attribute_value")
            if not attribute_value:
                attribute_value = ""
                result_string = result_string + attribute_value
            result_string = result_string + attribute_value
        elif "%" in t:
            t = re.findall(r"\d+", t)[0]
            result_string = result_string + t
        else:
            result_string = result_string + t
    return result_string


def parse_list_data(x, qs, list_data, list_index_queryset, parsed_list, list_all_parsed_digits):
    dict_data = {}
    year = x.year
    plan = x.plan
    attribute_value = x.attribute_value
    dict_data[list_index_queryset[0]] = {
        "attribute_value": attribute_value,
        "plan": plan,
        "year": year
    }

    for y in list_index_queryset[1:]:
        for z in list_data[y]:
            if (z.year == year) and (z.plan == plan):
                dict_data[y] = {
                    "attribute_value": z.attribute_value,
                    "plan": z.plan,
                    "year": z.year
                }
        if list(dict_data.keys()) == list_index_queryset:
            result_string = get_result_string(parsed_list, list_index_queryset, dict_data, plan, year, qs)
            total_digits = re.findall('\d+', result_string)
            try:
                result = eval(result_string)
            except SyntaxError:
                result = 0
            if PlanAnnualAttribute.objects.filter(plan=plan, year=year, plan_attribute_id=qs.id).exists():
                new = PlanAnnualAttribute.objects.get(
                    plan=plan, year=year, plan_attribute_id=qs.id)
                new.attribute_value = result
                new.save()
            else:
                PlanAnnualAttribute.objects.get_or_create(
                    plan=plan, year=year, plan_attribute_id=qs.id)


@shared_task
def generate_calculated_fields(list_ids):
    queryset = PlanAttribute.objects.filter(id__in=list_ids)
    print("in task")
    print(queryset)
    for qs in queryset:
        list_data, list_index_queryset, parsed_list, list_all_parsed_digits = parse_calculate_rule_string(qs=qs)
        print(list_data, list_index_queryset, parsed_list, list_all_parsed_digits)
        for x in list_data[list_index_queryset[0]]:
            parse_list_data(x, qs, list_data, list_index_queryset, parsed_list, list_all_parsed_digits)


@shared_task
def generate_calculated_fields_null(list_ids):
    queryset = PlanAttribute.objects.filter(id__in=list_ids)
    for qs in queryset:
        list_data, list_index_queryset, parsed_list, list_all_parsed_digits = parse_calculate_rule_string(
            qs=qs, attribute_value=True)
        for x in list_data[list_index_queryset[0]]:
            parse_list_data(x, qs, list_data, list_index_queryset, parsed_list, list_all_parsed_digits)


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
