import django_tables2 as tables
from django_tables2.utils import A
from .models import Plan, PlanAnnualAttribute, CensusAnnualAttribute


class PlanTable(tables.Table):
    census_plan_id = tables.LinkColumn('plan-detail', args=[A('pk')])
    display_name = tables.LinkColumn('plan-detail', args=[A('pk')])

    class Meta:
        model = Plan
        fields = ('census_plan_id', 'display_name',
                  'year_of_inception', 'year_closed', 'web_site',
                  'state_gov_role')
        attrs = {"class": "table-striped table-bordered"}
        empty_text = "There are no plans matching the search criteria..."


class PlanAnnualAttrTable(tables.Table):

    class Meta:
        model = PlanAnnualAttribute
        fields = ('year', 'plan_attribute', 'attribute_value')
        attrs = {"class": "table-striped table-bordered"}
        empty_text = "There are no records."


class CensusAnnualAttrTable(tables.Table):

    class Meta:
        model = CensusAnnualAttribute
        exclude = ('id', 'plan')
        attrs = {"class": "table-striped table-bordered"}
        empty_text = "There are no records."