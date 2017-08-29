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
from nested_admin import NestedTabularInline, NestedStackedInline, NestedModelAdmin
import copy

#### MODELS

from mysite.pensiondata.models import Plan, County, Government, County, State, GovernmentType, PlanAnnual, CensusPlanAnnualAttribute, PlanAttribute, PPDPlanAnnualAttribute

# class TabularPivotInline(InlineModelAdmin):
#     template = 'admin/edit_inline/tabular.html'

# class CensusPlanAnnualAttribute(ForeignKeyCacheMixin, admin.TabularInline):
#     model = CensusPlanAnnualAttribute
#     formset = PlanAnnualInlineFormset

# class MyInlineFormset(BaseInlineFormSet):


class PPDPlanAnnualAttributeInline(NestedTabularInline):

    model = PPDPlanAnnualAttribute
    verbose_name = 'PPD Data'
    verbose_name_plural = 'PPD Data'
    extra = 0
    classes = ['collapse']
    fields = [field.name for field in PPDPlanAnnualAttribute._meta.fields if field.name not in ['id', 'plan', 'data_source_id', 'year']]

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     field = super(PlanAnnualInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #     if db_field.name == "plan" and hasattr(self, "cached_plans"):
    #         field.choices = self.cached_plans
    #     return field

class CensusPlanAnnualAttributeInline(NestedTabularInline):
    
    model = CensusPlanAnnualAttribute
    verbose_name = 'Census Data'
    verbose_name_plural = 'Census Data'
    extra = 0
    classes = ['collapse']
    # fields = [field.name for field in CensusPlanAnnualAttribute._meta.fields if field.name not in ['id', 'plan', 'data_source_id', 'year']]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super(CensusPlanAnnualAttributeInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "plan_annual_id" and hasattr(self, "cached_census_plan_annual_attributes"):
            field.choices = self.cached_census_plan_annual_attributes
        return field

class PlanAnnualInline(NestedTabularInline):

    model = PlanAnnual
    verbose_name = 'Plan Year'
    verbose_name_plural = 'Plan Years'
    extra = 0

    # inlines = [CensusPlanAnnualAttributeInline, PPDPlanAnnualAttributeInline]
    inlines = [CensusPlanAnnualAttributeInline]
    # inlines = [PPDPlanAnnualAttributeInline]
    
    ordering = ['-year']
    readonly_fields = ['year']
    fields = ['year']
    can_delete = False

    # def get_formsets_with_inlines(self, request, obj=None):
    #     for inline in self.get_inline_instances(request, obj):
    #         inline.cached_plan_annuals = [(i.pk, str(i)) for i in CensusPlanAnnualAttribute.objects.filter(plan_id = obj.id).order_by('-year') ]
    #         yield inline.get_formset(request, obj), inline

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     print (db_field.name)
    #     field = super(PlanAnnualInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
    #     if db_field.name == "plan" and hasattr(self, "cached_plan_annuals"):
    #         field.choices = self.cached_plan_annuals
    #     return field

 # class PlanForm(forms.ModelForm):
 #    class Meta:
 #        model = Plan
 #    userinfo = forms.ModelChoiceField(queryset=UserInfo.objects.prefetch_related('user').all())       

#### PLAN
class PlanAdmin(NestedModelAdmin):
    
    model = Plan

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

    # def get_formsets_with_inlines(self, request, obj=None):
    #     for inline in self.get_inline_instances(request, obj):            
    #         inline.cached_plan_annuals = [(i.pk, str(i)) for i in PlanAnnual.objects.filter(plan_id = obj.id).order_by('-year') ]
    #         yield inline.get_formset(request, obj), inline



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




