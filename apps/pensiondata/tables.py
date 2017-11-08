import django_tables2 as tables
from django_tables2.utils import A
from .models import Plan


class PlanTable(tables.Table):
    census_plan_id = tables.LinkColumn('plan-detail', args=[A('pk')])
    display_name = tables.LinkColumn('plan-detail', args=[A('pk')])

    class Meta:
        model = Plan
        fields = ('census_plan_id', 'display_name')
        attrs = {"class": "table-striped table-bordered"}
        empty_text = "There are no plans matching the search criteria..."
