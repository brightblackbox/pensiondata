#########################################################################################################

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

# @formatter:off
from __future__ import unicode_literals

from django.db import connection, models
from django.core.validators import MaxValueValidator, MinValueValidator
import re
import datetime, decimal
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
    latitude = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)

    class Meta:
        db_table = 'government'
        verbose_name = 'Government'
        verbose_name_plural = 'Governments'

    def __str__(self):
        return "%s" % self.name


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


# custom model filed
class CharNullField(models.CharField):
    """
    Subclass of the CharField that allows empty strings to be stored as NULL.
    """
    description = "CharField that stores NULL but returns ''."

    def from_db_value(self, value, expression, connection, contex):
        """
        Gets value right out of the db and changes it if its ``None``.
        """
        if value is None:
            return ''
        else:
            return value

    def to_python(self, value):
        """
        Gets value right out of the db or an instance, and changes it if its ``None``.
        """
        if isinstance(value, models.CharField):
            # If an instance, just return the instance.
            return value
        if value is None:
            # If db has NULL, convert it to ''.
            return ''

        # Otherwise, just return the value.
        return value

    def get_prep_value(self, value):
        """
        Catches value right before sending to db.
        """
        if value == '':
            # If Django tries to save an empty string, send the db None (NULL).
            return None
        else:
            # Otherwise, just pass the value.
            return value


class Plan(models.Model):
    id = models.BigAutoField(primary_key=True)
    census_plan_id = CharNullField(max_length=255, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    year_of_inception = models.IntegerField(blank=True, null=True)
    benefit_tier = models.IntegerField(blank=True, null=True)
    year_closed = models.IntegerField(blank=True, null=True)
    web_site = models.CharField(max_length=255, blank=True, null=True)
    admin_gov = models.ForeignKey(Government, models.DO_NOTHING, blank=True, null=True,
                                  related_name='admin_gov')
    employ_gov = models.ForeignKey(Government, models.DO_NOTHING, blank=True, null=True,
                                   verbose_name="Employing Gov", related_name='employ_gov')
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
    system_assigned_employer_id = models.CharField(max_length=20, blank=True, null=True,
                                                   verbose_name="System Assigned Employer ID")
    latitude = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'plan'

    def __str__(self):
        return self.display_name or ''

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

    @staticmethod
    def get_master(plan):

        query = "select m.id, m.plan_id, m.year, p.plan_attribute_id, m.attribute_value " \
                "from plan_annual_master_attribute m " \
                "inner join plan_attribute_master p on m.plan_attribute_id = p.master_attribute_id " \
                "where m.plan_id=%s"

        return PlanAnnualMasterAttribute.objects.raw(query, [plan.id])

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


class PlanAnnualMasterAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    plan = models.ForeignKey('Plan', models.DO_NOTHING, null=True, blank=True)
    year = models.CharField(max_length=4)
    plan_attribute = models.ForeignKey('PlanAttribute', models.DO_NOTHING, null=True, blank=True)
    master_attribute = models.ForeignKey('PlanMasterAttributeNames', models.DO_NOTHING, null=True, blank=True)
    attribute_value = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        unique_together = ('plan', 'year', 'plan_attribute', 'master_attribute')
        db_table = 'plan_annual_master_attribute'
        verbose_name = 'Plan Annual Master Attribute'
        verbose_name_plural = 'Plan Annual Master Attributes'

    def __str__(self):
        return "Plan Annual Master Attribute(%s)" % self.year




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

class PlanAttributeMaster(models.Model):
    id = models.BigAutoField(primary_key = True)
    master_attribute = models.ForeignKey('PlanMasterAttributeNames', models.DO_NOTHING, null = True, blank = True, related_name = 'attr_master')
    plan_attribute = models.ForeignKey('PlanAttribute', models.DO_NOTHING, null = True, blank = True,)
    priority = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'plan_attribute_master'
        verbose_name = 'Plan Attribute to Master Mapping'


### THIS MODEL IS A WORK IN PROGRESS -- DO NOT USE FOR NOW
# class PlanInheritance(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     parent_plan = models.ForeignKey('Plan', models.DO_NOTHING, related_name='parent_plan_fk', null=True)
#     child_plan = models.ForeignKey('Plan', models.DO_NOTHING, related_name='child_plan_fk', null=True)
#     level = models.IntegerField()
#
#     class Meta:
#         managed = False
#         db_table = 'plan_inheritance'

class PlanMasterAttributeNames(models.Model):
    id = models.BigAutoField(primary_key = True)
    name = models.CharField(max_length = 255, blank = True, null = True)

    def __str__(self):
        return self.name

    class Meta:
        managed = True
        db_table = 'plan_master_attribute_names'
        verbose_name = 'Plan Master Attribute Name'
        verbose_name_plural = 'Plan Master Attribute Names'


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
        verbose_name = "Plan Benefit Design"

    def __str__(self):
        return self.plan_name


class PlanInheritance(models.Model):
    id = models.BigAutoField(primary_key=True)
    level = models.IntegerField(default=1,
                                validators=[
                                    MinValueValidator(1), MaxValueValidator(9)
                                ])
    child_plan = models.ForeignKey(Plan, on_delete=models.CASCADE, blank=True, null=True, related_name='child_plan')
    parent_plan = models.ForeignKey(Plan, on_delete=models.CASCADE, blank=True, null=True, related_name='parent_plan')

    class Meta:
        managed = False
        db_table = 'plan_inheritance'
        verbose_name_plural = "Plan Inheritance"


class ReportingTable(models.Model):
    id = models.BigAutoField(primary_key=True)
    plan = models.ForeignKey('Plan', models.DO_NOTHING, null=True, blank=True)
    census_plan_id = CharNullField(max_length=255, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    year_of_inception = models.IntegerField(blank=True, null=True)
    benefit_tier = models.IntegerField(blank=True, null=True)
    year_closed = models.IntegerField(blank=True, null=True)
    web_site = models.CharField(max_length=255, blank=True, null=True)
    admin_gov = models.ForeignKey(Government, models.DO_NOTHING, blank=True, null=True,
                                  related_name='admin_gov_report')
    employ_gov = models.ForeignKey(Government, models.DO_NOTHING, blank=True, null=True,
                                   verbose_name="Employing Gov", related_name='employ_gov_report')
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
    system_assigned_employer_id = models.CharField(max_length=20, blank=True, null=True,
                                                   verbose_name="System Assigned Employer ID")
    latitude = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True)

    year = models.CharField(max_length=4)

#@formatter:on
class PensionMapData(models.Model):
    class Meta:
        managed = False

    government_id = models.IntegerField()
    government_name = models.CharField(max_length = 255, blank = False)
    year = models.CharField(max_length = 4, blank = False, null = False)
    plan_contributions = models.DecimalField(decimal_places = 0, max_digits = 12)
    plan_liabilities = models.DecimalField(decimal_places = 0, max_digits = 12)

    @staticmethod
    def get_contributions(government_id, year = None):

        query = "select government.id, government.name as government_name, plan_annual_attribute.year, " \
                "sum(cast(plan_annual_attribute.attribute_value as numeric)) as employer_contribution " \
                "from plan, plan_annual_attribute, government, state " \
                "where plan.id = plan_annual_attribute.plan_id " \
                "and plan.admin_gov_id = government.id " \
                "and plan_attribute_id in (10885,10914,10984) " \
                "and government.state_id = state.id " \
                "and government.id=%s " \
                "and cast(year as numeric) <= %s " \
                "group by government.id, government.name, plan_annual_attribute.year " \
                "order by 2,3 desc"

        cur = connection.cursor()
        cur.execute(query, [government_id, year or datetime.datetime.now().year])

        columns = [c.name for c in cur.description]
        result = cur.fetchone()

        cur.close()

        if result is None:
            return None

        row = dict(zip(columns, result))

        return PensionMapData(
            government_id = row['id'],
            government_name = row['government_name'],
            year = row['year'],
            plan_contributions = row['employer_contribution']
        )

    @staticmethod
    def get_contributions_by_state(state, year = None):

        query = "select government.id, government.name as government_name, plan_annual_attribute.year, " \
                "sum(cast(plan_annual_attribute.attribute_value as numeric)) as employer_contribution " \
                "from plan, plan_annual_attribute, government, state " \
                "where plan.id = plan_annual_attribute.plan_id " \
                "and plan.admin_gov_id = government.id " \
                "and plan_attribute_id in (10885,10914,10984) " \
                "and government.state_id = state.id " \
                "and state.state_abbreviation = %s " \
                "and cast(year as numeric) <= %s " \
                "group by government.id, government.name, plan_annual_attribute.year " \
                "order by 2,3 desc"

        cur = connection.cursor()
        cur.execute(query, [state, year or datetime.datetime.now().year])

        columns = [c.name for c in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]

        cur.close()

        # only return the first row (latest year) for each government.id
        results = {}
        for row in rows:

            if row['id'] in results.keys():
                continue

            results[row['id']] = PensionMapData(
                government_id = row['id'],
                government_name = row['government_name'],
                year = row['year'],
                plan_contributions = row['employer_contribution']
            )

        return results.values()

    @staticmethod
    def get_liabilities(government_id, year = None):

        query = "select government.id, government.name as government_name, plan_annual_attribute.year, " \
                "sum(cast(plan_annual_attribute.attribute_value as numeric)) as employer_liabilities " \
                "from plan, plan_annual_attribute, government, state " \
                "where plan.id = plan_annual_attribute.plan_id " \
                "and plan.admin_gov_id = government.id " \
                "and plan_attribute_id in (10877) " \
                "and government.state_id = state.id " \
                "and government.id=%s " \
                "and cast(year as numeric) <= %s " \
                "group by government.id, government.name, plan_annual_attribute.year " \
                "order by 2,3 desc"

        cur = connection.cursor()
        cur.execute(query, [government_id, year or datetime.datetime.now().year])

        result = cur.fetchone()
        cur.close()

        if result is None:
            return None

        columns = [c.name for c in cur.description]
        row = dict(zip(columns, result))

        return PensionMapData(
            government_id = row['id'],
            government_name = row['government_name'],
            year = row['year'],
            plan_liabilities = row['employer_liabilities']
        )

    @staticmethod
    def get_liabilities_by_state(state, year = None):

        query = "select government.id, government.name as government_name, plan_annual_attribute.year, " \
                "sum(cast(plan_annual_attribute.attribute_value as numeric)) as employer_liabilities " \
                "from plan, plan_annual_attribute, government, state " \
                "where plan.id = plan_annual_attribute.plan_id " \
                "and plan.admin_gov_id = government.id " \
                "and plan_attribute_id in (10877) " \
                "and government.state_id = state.id " \
                "and state.state_abbreviation = %s " \
                "and cast(year as numeric) <= %s " \
                "group by government.id, government.name, plan_annual_attribute.year " \
                "order by 2,3 desc"

        cur = connection.cursor()
        cur.execute(query, [state, year or datetime.datetime.now().year])

        columns = [c.name for c in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]

        cur.close()

        # only return the first row (latest year) for each government.id
        results = {}
        for row in rows:

            if row['id'] in results.keys():
                continue

            results[row['id']] = PensionMapData(
                government_id = row['id'],
                government_name = row['government_name'],
                year = row['year'],
                plan_liabilities = row['employer_liabilities']
            )

        return results.values()


class PensionChartData(models.Model):
    class Meta:
        managed = False

    year = models.CharField(max_length = 4, blank = False, null = False)
    f1_header = models.CharField(max_length = 255, blank = False)
    f1_value = models.DecimalField(decimal_places = 0, max_digits = 12)
    f2_header = models.CharField(max_length = 255, blank = True)
    f2_value = models.DecimalField(decimal_places = 0, max_digits = 12)
    f3_header = models.CharField(max_length = 255, blank = True)
    f3_value = models.DecimalField(decimal_places = 0, max_digits = 12)
    f4_header = models.CharField(max_length = 255, blank = True)
    f4_value = models.DecimalField(decimal_places = 0, max_digits = 12)

    @staticmethod
    def get(government_id):
        query = "select distinct plan_annual_master_attribute.year, plan.display_name, " \
                "cast(plan_annual_master_attribute.attribute_value as numeric) as employer_contribution " \
                "from plan, plan_annual_master_attribute, government " \
                "where plan.id = plan_annual_master_attribute.plan_id " \
                "and plan.admin_gov_id = government.id " \
                "and master_attribute_id in (32,36) " \
                "and government.id=%s " \
                "and cast(plan_annual_master_attribute.attribute_value as numeric) <> 0 " \
                "order by 1,2"

        cur = connection.cursor()
        cur.execute(query, [government_id])
        data = cur.fetchall()
        cur.close()

        import pandas
        df = pandas.DataFrame(data, columns = ['year', 'display_name', 'employer_contribution'])
        pivoted = df.pivot(index = 'year', columns = 'display_name', values = 'employer_contribution')

        # map employer names to an indexed field (f1, f2, etc)
        header_map = {e:i+1 for i,e in enumerate(pivoted.keys())}

        results = []
        for year, values in pivoted.T.to_dict().items():
            item = PensionChartData(year = year)

            for name, contrib in values.items():
                i = header_map[name]
                setattr(item, 'f{}_header'.format(i), name)
                setattr(item, 'f{}_value'.format(i), contrib)

            results.append(item)

        return results


