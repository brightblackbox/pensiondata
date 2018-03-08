#########################################################################################################

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from __future__ import unicode_literals

from django.db import models
import re
#########################################################################################################

ATTRIBUTE_TYPE_CHOICES = (
    ('static', 'static'),
    ('calculated', 'calculated'),
)

PRESENTATIONS_EXROPT_CHOICES = (
    ('xlsx', 'xlsx'),
)

ATTRIBUTE_DATATYPES_CHOICES = (
    ('real', 'real'),
    ('int', 'int'),
    ('int_separated3', 'int_separated3'),
    ('text', 'text'),
    ('percentage', 'percentage'),
    ('percentage2', 'percentage2'),
    ('percentage4', 'percentage4'),
    ('yesno', 'yesno'),
    ('shortdate', 'shortdate')

)

SORTED_ATTRIBUTE_DATATYPES_CHOICES = sorted(
    ATTRIBUTE_DATATYPES_CHOICES, key=lambda x: x[1]
)

CALCULATED_STATUS_CHOICES = (
    ('in progress', 'in progress'),
    ('done', 'done')
)


class County(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    retirement_census_county_code = models.CharField(max_length=3, null=True, blank=True)
    retirement_census_state_code = models.CharField(max_length=2, null=True, blank=True)
    state = models.ForeignKey('State', models.DO_NOTHING, null=True, blank=True)

    class Meta:
        db_table = 'county'
        verbose_name_plural = 'Counties'

    def __str__(self):
        return self.name


class DataSource(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    trust_level = models.IntegerField()
    private = models.BooleanField(default=False, blank=True)

    class Meta:
        managed = True
        db_table = 'data_source'
        verbose_name = 'Data Source'
        verbose_name_plural = 'Data Sources'
        ordering = ('trust_level',)

    def __str__(self):
        return self.name

    @property
    def is_master_source(self):
        return self.id == 0  # NOTE: hardcodes


class AttributeCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=256)

    class Meta:
        managed = True
        verbose_name = 'Attribute Category'
        verbose_name_plural = 'Attribute Categories'
        db_table = 'attribute_category'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Government(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    state = models.ForeignKey('State', models.DO_NOTHING, null=True, blank=True)
    government_type = models.ForeignKey('GovernmentType', models.DO_NOTHING, null=True, blank=True)
    county = models.ForeignKey('County', models.DO_NOTHING, null=True, blank=True)

    class Meta:
        db_table = 'government'
        verbose_name = 'Government'
        verbose_name_plural = 'Governments'

    def __str__(self):
        return self.name


class GovernmentAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    data_source = models.ForeignKey('DataSource', models.DO_NOTHING, blank=True, null=True)
    datatype = models.CharField(max_length=256, choices=SORTED_ATTRIBUTE_DATATYPES_CHOICES, null=True, blank=True)
    attribute_category = models.ForeignKey('AttributeCategory', models.DO_NOTHING, blank=True, null=True)
    line_item_code = models.CharField(max_length=256, null=True, blank=True)
    display_order = models.IntegerField(null=True, blank=True)
    attribute_column_name = models.CharField(max_length=256, null=True, blank=True)
    multiplier = models.DecimalField(max_digits=30, decimal_places=6, null=True, blank=True, default=1000)
    weight = models.IntegerField(null=True, blank=True, default=0)

    # master attribute
    attributes_for_master = models.CharField('Source Attributes', max_length=256,
                                             null=True, blank=True,
                                             help_text='Source Attributes for the master attribute')

    # properties for value
    attribute_type = models.CharField(max_length=16, choices=ATTRIBUTE_TYPE_CHOICES, default='static')
    calculated_rule = models.TextField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'government_attribute'
        verbose_name = 'Government Attribute'
        verbose_name_plural = 'Government Attributes'
        unique_together = (('data_source', 'line_item_code'),)

    @property
    def is_static(self):
        return self.attribute_type == 'static'

    @property
    def category(self):
        if self.attribute_category is None:
            return ''
        return self.attribute_category.name

    @property
    def is_master_attribute(self):
        return self.data_source.is_master_source

    def __str__(self):
        return self.name


class GovernmentAttrSummary(models.Model):
    """
    This is a View in DB
    NOTE: readonly
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=256, null=True, blank=True)
    datatype = models.CharField(max_length=256, null=True, blank=True)
    line_item_code = models.CharField(max_length=256, null=True, blank=True)
    display_order = models.IntegerField(null=True, blank=True)
    attribute_column_name = models.CharField(max_length=256, null=True, blank=True)
    multiplier = models.DecimalField(max_digits=30, decimal_places=6, null=True, blank=True, default=1000)
    weight = models.IntegerField(default=0, null=True, blank=True)
    attributes_for_master = models.CharField('Source Attributes', max_length=256,
                                             null=True, blank=True,
                                             help_text='Source Attributes for the master attribute')

    attribute_type = models.CharField(max_length=16, choices=ATTRIBUTE_TYPE_CHOICES, default='static')
    calculated_rule = models.TextField(null=True, blank=True)

    data_source_id = models.IntegerField()
    attribute_category_id = models.IntegerField()
    data_source_name = models.CharField(max_length=255)
    attribute_category_name = models.CharField(max_length=256)

    class Meta:
        managed = False
        db_table = 'governmentattrview'


class GovernmentAnnualAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    government = models.ForeignKey(Government, models.DO_NOTHING, null=True, blank=True)
    year = models.CharField(max_length=4)
    government_attribute = models.ForeignKey('GovernmentAttribute', models.DO_NOTHING, null=True, blank=True, related_name='annual_attrs')
    attribute_value = models.CharField(max_length=256, null=True, blank=True)

    is_from_source = models.NullBooleanField(
        default=None,
        help_text='check if the value is from source or from user just for Master Attribute'
    )

    class Meta:
        unique_together = ('government', 'year', 'government_attribute',)
        db_table = 'government_annual_attribute'
        verbose_name = 'Government Annual Attribute'
        verbose_name_plural = 'Government Annual Attributes'

    def __str__(self):
        return "Government Annual Attribute(%s)" % self.year

    @property
    def data_source(self):
        return self.government_attribute.data_source.name

    @property
    def category(self):
        return self.government_attribute.attribute_category.name

    @property
    def value(self):
        """
        :return: string value
        """
        if self.government_attribute.is_master_attribute and self.is_from_source:
            print('here 1')
            attr_ids_for_master = self.government_attribute.attributes_for_master
            if attr_ids_for_master is None:
                return '0'
            else:
                attr_id_list = attr_ids_for_master.split(",")
                attr_id_list = list(map(int, attr_id_list))

                try:  # NOTE: if it is calculated_rule?
                    print(GovernmentAnnualAttribute.objects.filter(government=self.government, year=self.year,
                                                             government_attribute__id__in=attr_id_list))
                    obj = GovernmentAnnualAttribute.objects.filter(government=self.government, year=self.year,
                                                                   government_attribute__id__in=attr_id_list). \
                        order_by('-government_attribute__weight')[0]
                    return obj.attribute_value
                except Exception as e:
                    print(e.__dict__)
                    return '0'

        if self.government_attribute.is_static:
            return self.attribute_value

        stored_rule = self.government_attribute.calculated_rule
        calculated_rule = ''
        calc_items = re.split(r'#([\+\-\*\/\(\)]|\d+)#', stored_rule)

        for item in calc_items:
            if item == '':
                continue
            if '%' in item:
                static_value = re.findall(r'%(.+)%', item)[0]
                calculated_rule += static_value
            elif item in ['+', '-', '*', '/', '(', ')']:
                calculated_rule += item
            else:  # NOTE: pk should be integer
                pk = int(item)

                try:
                    item_val = GovernmentAnnualAttribute.objects.get(
                        government=self.government,
                        year=self.year,
                        government_attribute__id=pk
                    ).attribute_value

                    calculated_rule += item_val
                except GovernmentAnnualAttribute.DoesNotExist:
                    # print('Invalid: no operand')
                    return '0'
        try:
            value = eval(calculated_rule)
            return str(value)
        except:
            # print('Invalid: calculation error')
            return '0'


class GovernmentType(models.Model):
    id = models.BigAutoField(primary_key=True)
    level = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'government_type'
        verbose_name = 'Government Type'
        verbose_name_plural = 'Government Types'

    def __str__(self):
        return self.level


class Plan(models.Model):
    id = models.BigAutoField(primary_key=True)
    census_plan_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    year_of_inception = models.IntegerField(blank=True, null=True)
    benefit_tier = models.IntegerField(blank=True, null=True)
    year_closed = models.IntegerField(blank=True, null=True)
    web_site = models.CharField(max_length=255, blank=True, null=True)
    admin_gov = models.ForeignKey(Government, models.DO_NOTHING, blank=True, null=True)
    soc_sec_coverage = models.NullBooleanField()
    soc_sec_coverage_notes = models.CharField(max_length=255, blank=True, null=True)
    includes_state_employees = models.NullBooleanField()
    includes_local_employees = models.NullBooleanField()
    includes_safety_employees = models.NullBooleanField()
    includes_general_employees = models.NullBooleanField()
    includes_teachers = models.NullBooleanField()
    intra_period_data_entity_id = models.BigIntegerField(blank=True, null=True)
    intra_period_data_period_end_date = models.DateField(blank=True, null=True)
    intra_period_data_period_type = models.IntegerField(blank=True, null=True)
    gasb_68_type = models.CharField(max_length=30, blank=True, null=True)
    state_gov_role = models.CharField(max_length=30, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'plan'

    def __str__(self):
        return self.display_name

    # @property
    # def gov_state(self):
    # #     # return 'CO'
    #     return State.objects.values_list('state_abbreviation').first()
    # #     # return


class PlanAnnual(models.Model):
    id = models.BigAutoField(primary_key=True)
    plan = models.ForeignKey('Plan', models.DO_NOTHING, null=True, blank=True)
    year = models.CharField(max_length=4)
    government_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'plan_annual'

    def __str__(self):
        return "%s - %d" % (self.year, self.government_id)


class PlanAnnualAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    plan = models.ForeignKey('Plan', models.DO_NOTHING, null=True, blank=True)
    year = models.CharField(max_length=4)
    plan_attribute = models.ForeignKey('PlanAttribute', models.DO_NOTHING, null=True, blank=True, related_name='annual_attrs')
    attribute_value = models.CharField(max_length=256, null=True, blank=True)

    is_from_source = models.NullBooleanField(
        default=None,
        help_text='check if the value is from source or from user just for Master Attribute'
    )

    class Meta:
        unique_together = ('plan', 'year', 'plan_attribute',)
        db_table = 'plan_annual_attribute'
        verbose_name = 'Plan Annual Attribute'
        verbose_name_plural = 'Import Plan Annual Attributes'

    def __str__(self):
        return "Plan Annual Attribute(%s)" % self.year

    @property
    def data_source(self):
        return self.plan_attribute.data_source.name

    @property
    def category(self):
        return self.plan_attribute.attribute_category.name

    @property
    def value(self):
        """
        :return: string value
        """
        if self.plan_attribute.is_master_attribute and self.is_from_source:
            attr_ids_for_master = self.plan_attribute.attributes_for_master
            if attr_ids_for_master is None:
                return '0'
            else:
                attr_id_list = attr_ids_for_master.split(",")
                attr_id_list = list(map(int, attr_id_list))

                try:  # NOTE: if it is calculated_rule?
                    obj = PlanAnnualAttribute.objects.filter(plan=self.plan, year=self.year, plan_attribute__id__in=attr_id_list).\
                        order_by('-plan_attribute__weight')[0]
                    return obj.attribute_value
                except Exception as e:
                    print(e.__dict__)
                    return '0'

        if self.plan_attribute.is_static:
            return self.attribute_value

        stored_rule = self.plan_attribute.calculated_rule
        calculated_rule = ''
        calc_items = re.split(r'#([\+\-\*\/\(\)]|\d+)#', stored_rule)

        for item in calc_items:
            if item == '':
                continue
            if '%' in item:
                static_value = re.findall(r'%(.+)%', item)[0]
                calculated_rule += static_value
            elif item in ['+', '-', '*', '/', '(', ')']:
                calculated_rule += item
            else:  # NOTE: pk should be integer
                pk = int(item)

                try:
                    item_val = PlanAnnualAttribute.objects.get(
                        plan=self.plan,
                        year=self.year,
                        plan_attribute__id=pk
                    ).attribute_value

                    if not item_val:
                        item_val = ""

                    calculated_rule += item_val
                except PlanAnnualAttribute.DoesNotExist:
                    # print('Invalid: no operand')
                    return '0'
        try:
            value = eval(calculated_rule)
            return str(value)
        except:
            # print('Invalid: calculation error')
            return '0'


class PlanAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=256, unique=True, null=True, blank=True)
    data_source = models.ForeignKey('DataSource', models.DO_NOTHING, null=True, blank=True)
    datatype = models.CharField(max_length=256, choices=SORTED_ATTRIBUTE_DATATYPES_CHOICES, null=True, blank=True)
    attribute_category = models.ForeignKey('AttributeCategory', models.DO_NOTHING, null=True, blank=True)
    line_item_code = models.CharField(max_length=256)
    display_order = models.IntegerField(null=True, blank=True)
    attribute_column_name = models.CharField(max_length=256, null=True, blank=True)
    multiplier = models.DecimalField(max_digits=30, decimal_places=6, null=True, blank=True, default=1000)
    weight = models.IntegerField(null=True, blank=True, default=0)
    status_calculated = models.CharField(max_length=255, null=True, blank=True, choices=CALCULATED_STATUS_CHOICES)

    # master attribute
    attributes_for_master = models.CharField('Source Attributes', max_length=256,
                                             null=True, blank=True,
                                             help_text='Source Attributes for the master attribute')

    # properties for value
    attribute_type = models.CharField(max_length=16, choices=ATTRIBUTE_TYPE_CHOICES, default='static')
    calculated_rule = models.TextField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'plan_attribute'
        verbose_name = 'Plan Attribute'
        verbose_name_plural = 'Plan Attributes'
        unique_together = (('data_source', 'line_item_code'),)

    @property
    def is_static(self):
        return self.attribute_type == 'static'

    @property
    def category(self):
        if self.attribute_category is None:
            return ''
        return self.attribute_category.name

    @property
    def is_master_attribute(self):
        return self.data_source.is_master_source

    def __str__(self):
        return self.name

    def get_rule_readable(self):
        # e.g. #1# #+# #2# #*# #3# = 1+2*3
        if self.is_static:
            return ''

        stored_rule = self.calculated_rule
        readable_rule = ''
        calc_items = re.split(r'#([\+\-\*\/\(\)]|\d+)#', stored_rule)

        for item in calc_items:
            if item == '':
                continue
            if '%' in item:
                static_value = re.findall(r'%(.+)%', item)[0]
                readable_rule += static_value
            elif item in ['+', '-', '*', '/', '(', ')']:
                readable_rule += item
            else:  # NOTE: pk should be integer
                pk = int(item)

                try:
                    attr_name = PlanAttribute.objects.get(id=int(pk)).name  # NOTE: pk is string
                    readable_rule += attr_name
                except PlanAttribute.DoesNotExist:
                    return False
        return readable_rule


### THIS MODEL IS A WORK IN PROGRESS -- DO NOT USE FOR NOW
class PlanInheritance(models.Model):
    id = models.BigAutoField(primary_key=True)
    parent_plan = models.ForeignKey('Plan', models.DO_NOTHING, related_name='parent_plan_fk', null=True)
    child_plan = models.ForeignKey('Plan', models.DO_NOTHING, related_name='child_plan_fk', null=True)
    level = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'plan_inheritance'


class PlanProvisions(models.Model):
    id = models.OneToOneField('Plan', models.DO_NOTHING, db_column='id', primary_key=True)
    effective_date = models.DateField()
    sunset_date = models.DateField(blank=True, null=True)
    vesting_period = models.IntegerField(blank=True, null=True)
    early_retirement_age = models.IntegerField(blank=True, null=True)
    normal_retirement_age = models.IntegerField(blank=True, null=True)
    benefit_formula = models.CharField(max_length=30, blank=True, null=True)
    final_average_salary = models.CharField(max_length=100, blank=True, null=True)
    multiplier = models.CharField(max_length=100, blank=True, null=True)
    benefit_supplement = models.CharField(max_length=100, blank=True, null=True)
    early_retirement_penalty = models.CharField(max_length=100, blank=True, null=True)
    early_retirement_formula = models.CharField(max_length=100, blank=True, null=True)
    cost_of_living_adjustment = models.CharField(max_length=100, blank=True, null=True)
    deferred_vested_start_date = models.CharField(max_length=100, blank=True, null=True)
    mandatory_retirement = models.NullBooleanField()
    deferred_retirement_option_program = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'plan_provisions'


class State(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.TextField()
    state_abbreviation = models.CharField(max_length=2, null=True, blank=True)
    retirement_census_state_code = models.CharField(max_length=2, null=True, blank=True)

    class Meta:
        db_table = 'state'

    def __str__(self):
        return self.name


class ExportGroup(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, default='Presentation Export')
    export_type = models.CharField(max_length=30, choices=PRESENTATIONS_EXROPT_CHOICES, default='xlsx')
    active = models.BooleanField(default=True)

    def __str__(self):
        return "{name}: {format}".format(name=self.name, format=self.export_type)


class PresentationExport(models.Model):
    id = models.BigAutoField(primary_key=True)
    export_group = models.ForeignKey(ExportGroup, default=1)
    plan_field = models.ForeignKey(PlanAttribute, null=True, blank=True)
    government_field = models.ForeignKey(GovernmentAttribute, null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'presentation_export'
        unique_together = (
            ('export_group', 'plan_field'),
            ('export_group', 'government_field')
        )

    def __str__(self):
        name = "{name}: {field} - {order}"
        field = ''
        if self.plan_field:
            field = self.plan_field.name
        elif self.government_field:
            field = self.government_field.name
        return name.format(name=self.export_group.name, field=field, order=self.order)


class PlanBenefitDesign(models.Model):
    plan = models.OneToOneField(Plan, on_delete=models.CASCADE, blank=True, null=True)
    slepp_record_id = models.CharField(max_length=255, blank=True, null=True)
    plan_name = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    occupation = models.CharField(max_length=255, blank=True, null=True)
    tier = models.CharField(max_length=255, blank=True, null=True)
    hired_before_date = models.DateField(blank=True, null=True)
    hired_on_or_after_date = models.DateField(blank=True, null=True)
    covers_new_hires = models.FloatField(blank=True, null=True)
    plan_type = models.CharField(max_length=255, blank=True, null=True)
    employee_contribution_rate = models.FloatField(blank=True, null=True)
    vesting_years = models.FloatField(blank=True, null=True)
    retirement_eligibility_normal = models.CharField(max_length=255, blank=True, null=True)
    retirement_eligibility_early = models.CharField(max_length=255, blank=True, null=True)
    formula_benefit = models.CharField(max_length=255, blank=True, null=True)
    final_average_salary = models.CharField(max_length=255, blank=True, null=True)
    multiplier = models.CharField(max_length=255, blank=True, null=True)
    benefit_supplement = models.TextField(blank=True, null=True)
    penalty_for_early_retirement = models.CharField(max_length=255, blank=True, null=True)
    early_retirement_formula = models.CharField(max_length=255, blank=True, null=True)
    additional_details_on_early_retirement_penalties = models.CharField(max_length=255, blank=True, null=True)
    cost_of_living_adjustment = models.CharField(max_length=255, blank=True, null=True)
    deferred_vested_start_date = models.CharField(max_length=255, blank=True, null=True)
    increases_in_deferred_vested_benefits = models.CharField(max_length=255, blank=True, null=True)
    mandatory_retirement = models.CharField(max_length=255, blank=True, null=True)
    deferred_retirement_option_program = models.FloatField(blank=True, null=True)
    vesting_in_years_non_fas_plan = models.CharField(max_length=255, blank=True, null=True)
    employer_contribution_rate_non_fas_plan = models.CharField(max_length=255, blank=True, null=True)
    employee_contribution_ratenon_fas_plan = models.CharField(max_length=255, blank=True, null=True)
    interest_rate_non_fas_plan = models.CharField(max_length=255, blank=True, null=True)
    social_security_coverage = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'plan_benefit_design'

    def __str__(self):
        return self.plan_name
