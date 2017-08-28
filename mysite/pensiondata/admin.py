"""
Customizations for the Django administration interface.
"""

# from django.contrib import admin
# from app.models import Choice, Poll

# class ChoiceInline(admin.TabularInline):
#     """Choice objects can be edited inline in the Poll editor."""
#     model = Choice
#     extra = 3

# class PollAdmin(admin.ModelAdmin):
#     """Definition of the Poll editor."""
#     fieldsets = [
#         (None, {'fields': ['text']}),
#         ('Date information', {'fields': ['pub_date']}),
#     ]
#     inlines = [ChoiceInline]
#     list_display = ('text', 'pub_date')
#     list_filter = ['pub_date']
#     search_fields = ['text']
#     date_hierarchy = 'pub_date'

# admin.site.register(Poll, PollAdmin)

"""
Customizations for the Django administration interface.
"""

from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from django import forms
from nested_admin import NestedTabularInline, NestedModelAdmin
import copy

#### MODELS

from mysite.pensiondata.models import Plan, County, Government, County, State, GovernmentType, PlanAnnual, CensusPlanAnnualAttribute, PlanAttribute

# class TabularPivotInline(InlineModelAdmin):
#     template = 'admin/edit_inline/tabular.html'

# class CensusPlanAnnualAttribute(ForeignKeyCacheMixin, admin.TabularInline):
#     model = CensusPlanAnnualAttribute
#     formset = PlanAnnualInlineFormset

# class MyInlineFormset(BaseInlineFormSet):


class CensusPlanAnnualAttributeInline(NestedTabularInline):
    
    model = CensusPlanAnnualAttribute
    verbose_name = 'Census Data'
    verbose_name_plural = 'Census Data'
    extra = 0
    classes = ['collapse']
    fields = [field.name for field in CensusPlanAnnualAttribute._meta.fields if field.name not in ['id', 'plan_id', 'data_source_id', 'year']]

class PlanAnnualInline(NestedTabularInline):
    
    model = PlanAnnual
    verbose_name = 'Plan Year'
    verbose_name_plural = 'Plan Years'
    extra = 0
    inlines = [CensusPlanAnnualAttributeInline]

    ordering = ['-year']

    # fields = ['year']

    readonly_fields = ['year']
    fields = ['year']
    can_delete = False

    # def get_queryset(self, request):
    #     """Alter the queryset to return no existing entries"""
    #     # get the existing query set, then empty it.
    #     qs = super(PlanAnnualInline, self).get_queryset(request)
    #     return qs

    # readonly_fields = ['year', 'plan_attribute']
    # fields = ['year', 'census_attribute']


    # def census_attribute(self, obj):
    #     return CensusPlanAnnualAttribute.objects.filter(plan_annual.id == obj.id)

#### PLAN
class PlanAdmin(NestedModelAdmin):
    """Definition of the Plan editor."""
    fieldsets = [
        ('Plan', {
            'fields': [field.name for field in Plan._meta.fields if field.name != 'id']
        }),
    ]

    list_display = ('census_plan_id', 'name')
    list_filter = ['name']
    search_fields = ['name']

    inlines = [PlanAnnualInline]

    class Media:
        css = { "all" : ("app/content/planadmin.css",) }

    # year = '2017'    

admin.site.register(Plan, PlanAdmin)

#### COUNTY
class CountyAdmin(admin.ModelAdmin):
    """Definition of the Plan editor."""
    fieldsets = [
        (None, {'fields': [field.name for field in County._meta.fields if field.name != 'id']})
    ]
    list_display = ('name', 'county_fips_code')
    list_filter = ['name']
    search_fields = ['name']

admin.site.register(County, CountyAdmin)

#### STATE
class StateAdmin(admin.ModelAdmin):
    """Definition of the Plan editor."""
    fieldsets = [
        (None, {'fields': [field.name for field in State._meta.fields if field.name != 'id']})
    ]
    list_display = ('name', 'state_fips_code')
    list_filter = ['name']
    search_fields = ['name']

admin.site.register(State, StateAdmin)

#### GOVERNMENT TYPE
class GovernmentTypeAdmin(admin.ModelAdmin):
    """Definition of the Plan editor."""
    fieldsets = [
        (None, {'fields': [field.name for field in GovernmentType._meta.fields if field.name != 'id']})
    ]
    list_display = ('id', 'level')
    list_filter = ['level']
    search_fields = ['level']

admin.site.register(GovernmentType, GovernmentTypeAdmin)

#### GOVERNMENT TYPE
class GovernmentAdmin(admin.ModelAdmin):
    """Definition of the Plan editor."""
    fieldsets = [
        (None, {'fields': [field.name for field in Government._meta.fields if field.name != 'id']})
    ]
    list_display = ('id', 'name')
    list_filter = ['name']
    search_fields = ['name']

admin.site.register(Government, GovernmentAdmin)

#### PLAN ATTRIBUTE
class PlanAttributeAdmin(admin.ModelAdmin):
    """Definition of the Plan editor."""
    fieldsets = [
        (None, {'fields': [field.name for field in PlanAttribute._meta.fields if field.name != 'id']})
    ]
    list_display = ('id', 'attribute')
    list_filter = ['attribute']
    search_fields = ['attribute']

admin.site.register(PlanAttribute, PlanAttributeAdmin)




