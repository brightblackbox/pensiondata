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


class CensusData(models.Model):
    id = models.BigAutoField(primary_key=True)
    state_contribution_for_local_employees = models.DecimalField(max_digits=10, decimal_places=6)

    class Meta:
        managed = True
        db_table = 'census_data'


class County(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    retirement_census_county_code = models.CharField(max_length=3)
    retirement_census_state_code = models.CharField(max_length=2)
    state = models.ForeignKey('State', models.DO_NOTHING, null=True, blank=True)

    class Meta:
        db_table = 'county'

    def __str__(self):
        return self.name


class DataSource(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    trust_level = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'data_source'

    def __str__(self):
        return self.name


class Government(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    state = models.ForeignKey('State', models.DO_NOTHING, null=True, blank=True)
    government_type = models.ForeignKey('GovernmentType', models.DO_NOTHING, null=True, blank=True)
    county = models.ForeignKey(County, models.DO_NOTHING, null=True, blank=True)

    class Meta:
        db_table = 'government'

    def __str__(self):
        return self.name


class GovernmentAnnual(models.Model):
    id = models.BigAutoField(primary_key=True)
    government = models.ForeignKey(Government, models.DO_NOTHING, null=True, blank=True)
    government_attribute = models.ForeignKey('GovernmentAttribute', models.DO_NOTHING, null=True, blank=True)
    attribute_value = models.TextField()

    class Meta:
        managed = True
        db_table = 'government_annual'


class GovernmentAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    attribute_key = models.TextField()
    attribute_datatype = models.IntegerField()
    attribute_category = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'government_attribute'


class GovernmentType(models.Model):
    id = models.BigAutoField(primary_key=True)
    level = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'government_type'

    def __str__(self):
        return self.level


class Plan(models.Model):
    id = models.BigAutoField(primary_key=True)
    census_plan_id = models.CharField(max_length=255)
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
        return self.name

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
    # census_plan_annual = models.OneToOneField('CensusPlanAnnualAttribute', models.DO_NOTHING, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'plan_annual'

    def __str__(self):
        return "%s - %d" % (self.year, self.government_id)


class PlanAnnualAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    # plan_annual = models.ForeignKey('PlanAnnual', models.DO_NOTHING, null=True, blank=True)
    plan = models.ForeignKey('Plan', models.DO_NOTHING, null=True, blank=True)
    year = models.CharField(max_length=4)
    plan_attribute = models.ForeignKey('PlanAttribute', models.DO_NOTHING, null=True, blank=True)
    attribute_value = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        # unique_together = ('plan', 'year', 'plan_attribute',)
        db_table = 'plan_annual_attribute'

    def __str__(self):
        return "PlanAnnualAttribute(%s)" % self.year

    @property
    def data_source(self):
        return self.plan_attribute.data_source.name

    @property
    def category(self):
        return self.plan_attribute.plan_attribute_category.name

    @property
    def value(self):
        """
        :return: string value
        """
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


class PlanAttributeCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=256)

    class Meta:
        managed = True
        verbose_name = 'Attribute category'
        verbose_name_plural = 'Attribute categories'
        db_table = 'plan_attribute_category'

    def __str__(self):
        return self.name


class PlanAttributeMaster(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=256)
    datatype = models.CharField(max_length=256)
    plan_attribute_category = models.ForeignKey('PlanAttributeCategory', models.DO_NOTHING, null=True, blank=True)
    display_order = models.IntegerField()
    attribute_column_name = models.CharField(max_length=256)

    class Meta:
        managed = True
        verbose_name = 'Master attribute'
        verbose_name_plural = 'Master attributes'
        db_table = 'plan_attribute_master'

    def __str__(self):
        return self.name


class PlanAttribute(models.Model):
    ATTRIBUTE_TYPE_CHOICES = (
        ('static', 'static'),
        ('calculated', 'calculated'),
    )

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=256, unique=True, null=True, blank=True)
    datatype = models.CharField(max_length=256, null=True, blank=True)
    plan_attribute_category = models.ForeignKey('PlanAttributeCategory', models.DO_NOTHING, null=True, blank=True)
    line_item_code = models.CharField(max_length=256)
    display_order = models.IntegerField(null=True, blank=True)
    attribute_column_name = models.CharField(max_length=256, null=True, blank=True)
    multiplier = models.DecimalField(max_digits=30, decimal_places=6, null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)
    plan_attribute_master = models.ForeignKey('PlanAttributeMaster', models.DO_NOTHING, null=True, blank=True)
    data_source = models.ForeignKey('DataSource', models.DO_NOTHING, null=True, blank=True)

    attribute_type = models.CharField(max_length=16, choices=ATTRIBUTE_TYPE_CHOICES, default='static')
    calculated_rule = models.TextField(null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'plan_attribute'

    @property
    def is_static(self):
        return self.attribute_type == 'static'

    @property
    def category(self):
        if self.plan_attribute_category is None:
            return ''
        return self.plan_attribute_category.name

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
    state_abbreviation = models.CharField(max_length=2)
    retirement_census_state_code = models.CharField(max_length=2)

    class Meta:
        db_table = 'state'

    def __str__(self):
        return self.name

################################################################################################################################################################
################################################################################################################################################################
### THE FOLLOWING MODELS REFER TO DATABASE VIEWS THAT CONVERT ATTRIBUTE ROWS FROM PLAN_ANNUAL_ATTRIBUTES INTO COLUMNS WITH ONE ROW PER PLAN PER YEAR
### THESE ARE STILL UNDER CONSTRUCTION AND SHOULD NOT BE USED -- IF NEEDED PLEASE REACH OUT TO NICK@BRIGHTBLACKBOX.COM
################################################################################################################################################################
################################################################################################################################################################

class CensusAnnualAttribute(models.Model):

    id = models.BigIntegerField(primary_key=True)
    plan = models.ForeignKey('Plan', on_delete=models.DO_NOTHING,null=True, blank=True)
    year = models.CharField(max_length=4)

    other_investment_earnings = models.BigIntegerField()
    losses_on_investments = models.BigIntegerField()
    total_earnings_on_investments = models.BigIntegerField()
    rentals_from_state_government = models.BigIntegerField()
    employees_receiving_lump_sum_payments = models.BigIntegerField()
    survivors_receiving_lump_sum_payments = models.BigIntegerField()
    monthly_payments_to_retirees = models.BigIntegerField()
    monthly_payments_to_disabled = models.BigIntegerField()
    monthly_payments_to_survivors = models.BigIntegerField()
    monthly_lump_sum_payments_to_members = models.BigIntegerField()
    monthly_lump_sum_payments_to_survivors = models.BigIntegerField()
    federally_sponsored_agencies_at_book_value = models.BigIntegerField()
    members_covered_by_social_security = models.BigIntegerField()
    corporate_bonds_other_at_book_value = models.BigIntegerField()
    amounts_transmitted_to_federal_social_security_system = models.BigIntegerField()
    all_other_short_term_investments = models.BigIntegerField()
    total_cash_and_short_term_investments = models.BigIntegerField()
    federal_agency_securities = models.BigIntegerField()
    federal_treasury_securities = models.BigIntegerField()
    federally_sponsored_agencies = models.BigIntegerField()
    total_federal_government_securities = models.BigIntegerField()
    corporate_bonds_other = models.BigIntegerField()
    total_corporate_bonds = models.BigIntegerField()
    mortgages_held_directly = models.BigIntegerField()
    corporate_stocks = models.BigIntegerField()
    investments_held_in_trust_by_other_agencies = models.BigIntegerField()
    state_and_local_government_securities = models.BigIntegerField()
    foreign_and_international_securities = models.BigIntegerField()
    other_securities = models.BigIntegerField()
    total_other_investments = models.BigIntegerField()
    real_property = models.BigIntegerField()
    other_investments = models.BigIntegerField()
    receipts_for_transmittal_to_fed_social_security_system = models.BigIntegerField()
    total_cash_and_securities = models.BigIntegerField()
    actuarially_accured_liabilities = models.BigIntegerField()
    state_government_active_members = models.BigIntegerField()
    local_government_active_members = models.BigIntegerField()
    total_active_members = models.BigIntegerField()
    inactive_members = models.BigIntegerField()
    retirement_benefits = models.BigIntegerField()
    survivor_benefits = models.BigIntegerField()
    other_benefits = models.BigIntegerField()
    total_benefit_payments = models.BigIntegerField()
    withdrawals = models.BigIntegerField()
    administrative_expenses = models.BigIntegerField()
    time_or_savings_deposits = models.BigIntegerField()
    cash_on_hand_and_demand_deposits = models.BigIntegerField()
    former_active_members_retired_on_account_of_disability = models.BigIntegerField()
    survivors = models.BigIntegerField()
    covered_payroll = models.BigIntegerField()
    members_retired_on_account_of_age_or_service = models.BigIntegerField()
    total_state_contributions = models.BigIntegerField()
    system_category = models.BigIntegerField()
    coverage_type = models.BigIntegerField()
    membership_basis = models.BigIntegerField()
    do_employees_contribute = models.BigIntegerField()
    optional_benefits_available = models.BigIntegerField()
    vesting_period = models.BigIntegerField()
    corporate_bonds_at_book_value = models.BigIntegerField()
    corporate_stocks_at_book_value = models.BigIntegerField()
    contributions_by_state_employees = models.BigIntegerField()
    foreign_and_international_securities_sameasz70 = models.BigIntegerField()
    contributions_by_local_employees = models.BigIntegerField()
    state_contributions_on_behalf_of_state_employees = models.BigIntegerField()
    state_contributions_on_behalf_of_local_employees = models.BigIntegerField()
    local_government_contributions = models.BigIntegerField()
    contributions_from_parent_local_governments = models.BigIntegerField()
    interest_earnings = models.BigIntegerField()
    dividend_earnings = models.BigIntegerField()
    net_gains_on_investments = models.BigIntegerField()
    other_payments = models.BigIntegerField()
    other_receipts = models.BigIntegerField()
    total_other_securities = models.BigIntegerField()
    current_year_liabilities = models.BigIntegerField()
    disability_benefits = models.BigIntegerField()

    #### Attempt to programatically generate the model columns
    # data_source_id = 1
    # cols = PlanAttribute.objects.all()
    # for col in cols:
    #     if col.data_source_id == data_source_id and col.attribute_column_name not in ['id', 'plan_id', 'year']:
    #         locals()[col.attribute_column_name] = models.CharField(max_length=256)

    class Meta:
        managed = False
        db_table = 'census_annual_attribute_mv'

class PPDAnnualAttribute(models.Model):

    id = models.BigIntegerField(primary_key=True)
    plan = models.ForeignKey('Plan', on_delete=models.DO_NOTHING,null=True, blank=True)
    year = models.CharField(max_length=4)

    uppercorridor=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    lowercorridor=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actcostmethcode=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    dataentrycode=models.CharField(max_length=256)
    source_gasbassumptions=models.CharField(max_length=256)
    actcostmeth_gasb=models.CharField(max_length=256)
    assetvalmeth_gasb=models.CharField(max_length=256)
    fundingmeth_gasb=models.CharField(max_length=256)
    cola_verabatim=models.CharField(max_length=256)
    cola_code=models.CharField(max_length=256)
    source_fundingandmethods=models.CharField(max_length=256)
    assetvalmeth=models.CharField(max_length=256)
    phasein=models.CharField(max_length=256)
    assetvalmeth_note=models.CharField(max_length=256)
    actcostmeth=models.CharField(max_length=256)
    actcostmeth_note=models.CharField(max_length=256)
    fundingmeth=models.CharField(max_length=256)
    fundmethcode_1=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    arc=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    fundmethcode_2=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    payrollgrowthassumption=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    totamortperiod=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    plan_annual_id=models.BigIntegerField()
    remainingamortperiod=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actassets_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actliabilities_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actfundedratio_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    uaal_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actliabilities_other=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    payroll=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    requiredcontribution=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    percentreqcontpaid=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    percentarcpaid=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    totalpensionliability=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    netposition=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    netpensionliability=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    adec=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    aec=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    coveredpayroll_gasb67=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    percentadec=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actassets_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actliabilities_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actfundedratio_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    requiredcontribution_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actfundedratio_gasb67=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_1yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    uaalyearestablished=models.CharField(max_length=256)
    investmentreturn_2yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_3yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_4yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_5yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_7yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_8yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_10yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_12yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_15yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_20yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_25yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_30yr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    grossreturns=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    georeturn_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    geogrowth_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_1yr_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_5yr_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_10yr_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    equities_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    equities_domestic=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    equities_international=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    fixedincome_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    fixedincome_domestic=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    fixedincome_international=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actvaldate_gasbschedules=models.DateField(blank=True, null=True)
    cashandshortterm=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    alternatives=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    other=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    contrib_ee_regular=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    contrib_er_regular=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    contrib_er_state=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    contrib_ee_purchaseservice=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    investmentreturn_longterm=models.CharField(max_length=256)
    investmentreturn_longtermstartye=models.CharField(max_length=256)
    source_assetallocation=models.CharField(max_length=256)
    income_securitieslending=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_securitieslending=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    income_securitieslendingrebate=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    income_otheradditions=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    income_net=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_totbenefits=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_retbenefits=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_disabilitybenefits=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_deathbenefits=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_dropbenefits=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_survivorbenefits=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_colabenefits=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_lumpsumbenefits=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_otherbenefits=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_refunds=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_adminexpenses=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_depreciation=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_otherdeductions=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    adjustment_mktassets=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    mktassets_net=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    contributionfy=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    normcostrate_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    normcostrate_ee=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    normcostrate_er=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    reqcontrate_er=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    reqcontrate_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    normcostamount_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    normcostamount_ee=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    normcostamount_er=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    reqcontamount_er=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    reqcontamount_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    normcostrate_tot_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    normcostrate_ee_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    normcostrate_er_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    reqcontrate_er_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    projectedpayroll=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actives_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    activesalaries=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    activeage_avg=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    activetenure_avg=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    activesalary_avg=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    inactivevestedmembers=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    inactivenonvested=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    beneficiaries_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    benefits_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    beneficiaryage_avg=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    beneficiarybenefit_avg=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    beneficiaries_serviceretirees=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    benefits_serviceretirees=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    serviceretireeage_avg=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    serviceretireebenefit_avg=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    source_incomestatement=models.CharField(max_length=256)
    fairvaluechange_seclend=models.CharField(max_length=256)
    expense_seclendmgmtfees=models.CharField(max_length=256)
    fairvaluechange_seclendug=models.CharField(max_length=256)
    source_actcosts=models.CharField(max_length=256)
    serviceretage_avg=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    servicerettenure_avg=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    serviceretbenefit_avg=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    benefits_disabilityretirees=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    beneficiaries_survivors=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    beneficiaries_spousalsurvivors=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    source_actliabilities=models.CharField(max_length=256)
    investmentreturnassumption_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actcostmethcode_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    assetvalmethcode_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    planleveldata=models.BigIntegerField()
    planname=models.CharField(max_length=256)
    fy=models.CharField(max_length=256)
    planfullname=models.CharField(max_length=256)
    source_planbasics=models.CharField(max_length=256)
    planinceptionyear=models.CharField(max_length=256)
    planyearclosed=models.CharField(max_length=256)
    stateabbrev=models.CharField(max_length=256)
    statename=models.CharField(max_length=256)
    govtname=models.CharField(max_length=256)
    employeetypecovered=models.CharField(max_length=256)
    socseccovered_verbatim=models.CharField(max_length=256)
    coststructure=models.CharField(max_length=256)
    benefitswebsite=models.CharField(max_length=256)
    reportingdatenotes=models.CharField(max_length=256)
    fundingmeth_note=models.CharField(max_length=256)
    pvfb_other=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    pvfb_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    pvfnc_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    pvfnc_ee=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    pvfnc_er=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    pvfs=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    mktassets_actrpt=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actassets_ava=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actliabilities_ean=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actliabilities_puc=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    nocafr=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    noav=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    uaalrate=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    plantype=models.BigIntegerField()
    gainlossconcept=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    socseccovered=models.BigIntegerField()
    gainlossbase_1=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    gainlossbase_2=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    employertype=models.BigIntegerField()
    costsharing=models.BigIntegerField()
    stateemployers=models.BigIntegerField()
    localemployers=models.BigIntegerField()
    schoolemployers=models.BigIntegerField()
    coversstateemployees=models.BigIntegerField()
    coverslocalemployees=models.BigIntegerField()
    coversteachers=models.BigIntegerField()
    stategenee=models.BigIntegerField()
    localgenee=models.BigIntegerField()
    statepolice=models.BigIntegerField()
    localpolice=models.BigIntegerField()
    statefire=models.BigIntegerField()
    localfire=models.BigIntegerField()
    teacher=models.BigIntegerField()
    schoolees=models.BigIntegerField()
    judgesattorneys=models.BigIntegerField()
    electedofficials=models.BigIntegerField()
    gainloss=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    gainlossperiod=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    eegroupid=models.BigIntegerField()
    tierid=models.BigIntegerField()
    cafr_cy=models.BigIntegerField()
    actrpt_cy=models.BigIntegerField()
    cafr_av_conflict=models.BigIntegerField()
    actrptdate=models.DateField(blank=True, null=True)
    fye=models.DateField(blank=True, null=True)
    inflationassumption_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    phaseinpercent=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    phaseinperiods=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    phaseintype=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    gainlossrecognition=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    assetsmoothingbaseline=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expectedreturnmethod=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    addsubtractgainloss=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actvaldate_gasbassumptions=models.DateField(blank=True, null=True)
    assetsmoothingperiod_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    ppd_id=models.BigIntegerField()
    fundingmethcode1_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    fundingmethcode2_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    system_id=models.BigIntegerField()
    valuationid=models.BigIntegerField()
    uaalamortperiod_gasb=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    blendeddiscountrate=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    inpfs=models.BigIntegerField()
    fiscalyeartype=models.BigIntegerField()
    mktassets_smooth=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    planclosed=models.BigIntegerField()
    actassets_smooth=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    administeringgovt=models.BigIntegerField()
    netflows_smooth=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    assetvalmethcode=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    smoothingreset=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    wageinflation=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    contrib_ee_other=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    contrib_er_other=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    contrib_other=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    contrib_tot=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    fairvaluechange_investments=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    fairvaluechange_realestate=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    income_interest=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    income_dividends=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    income_interestanddividends=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    income_realestate=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    income_privateequity=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    income_alternatives=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    income_international=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    income_otherinvestments=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_realestate=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_privateequity=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_alternatives=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_otherinvestments=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    expense_investments=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    source_gasbschedules=models.CharField(max_length=256)
    aj=models.CharField(max_length=256)
    ak=models.CharField(max_length=256)
    source_investmentreturn=models.CharField(max_length=256)
    expense_net=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    beneficiaries_other=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    dropmembers=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    othermembers=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    totmembership=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    activesalary_avg_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    beneficiarybenefit_avg_est=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    pvfb_inactivenonvested=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    pvfb_active=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    pvfb_inactivevested=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    pvfb_retiree=models.DecimalField(max_digits=19, decimal_places=6, blank=True, null=True)
    actvaldate_actuarialcosts=models.CharField(max_length=256)
    source_membership=models.CharField(max_length=256)
    beneficiaries_disabilityretirees=models.CharField(max_length=256)
    beneficiaries_dependentsurvivors=models.CharField(max_length=256)

    class Meta:
        managed = False
        db_table = 'ppd_annual_attribute'

# class ReasonData(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     fiscal_year = models.IntegerField()
#     fiscal_year_end_date = models.DateField()
#     adec = models.TextField(blank=True, null=True)  # This field type is a guess.
#     adec_paid = models.TextField(blank=True, null=True)  # This field type is a guess.
#     adec_missed = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     percent_of_adec_paid = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     fiduciary_net_position_or_mva = models.TextField(blank=True, null=True)  # This field type is a guess.
#     total_pension_liability_or_aal = models.TextField(blank=True, null=True)  # This field type is a guess.
#     net_pension_liability_or_ual = models.TextField(blank=True, null=True)  # This field type is a guess.
#     funded_ratio_gasb_67_68 = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     net_pension_liability_using_rate_minus_1 = models.TextField(blank=True, null=True)  # This field type is a guess.
#     net_pension_liability_using_rate_plus_1 = models.TextField(blank=True, null=True)  # This field type is a guess.
#     actuarially_required_contribution = models.TextField(blank=True, null=True)  # This field type is a guess.
#     total_arc_paid = models.TextField(blank=True, null=True)  # This field type is a guess.
#     total_arc_missed = models.TextField(blank=True, null=True)  # This field type is a guess.
#     percent_of_arc_paid = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     actuarial_value_of_assets = models.TextField(blank=True, null=True)  # This field type is a guess.
#     actuarial_acrrued_liability = models.TextField(blank=True, null=True)  # This field type is a guess.
#     unfunded_accrued_liability = models.TextField(blank=True, null=True)  # This field type is a guess.
#     funded_ratio_gasb_25 = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     covered_payroll = models.TextField(blank=True, null=True)  # This field type is a guess.
#     adec_as_a_percent_of_payroll = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     arc_as_a_percent_of_payroll = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     market_value_of_assets = models.TextField(blank=True, null=True)  # This field type is a guess.
#     market_value_funded_ratio = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     total_actuarial_gain_loss = models.TextField(blank=True, null=True)  # This field type is a guess.
#     benefit_payments = models.TextField(blank=True, null=True)  # This field type is a guess.
#     refunds = models.TextField(blank=True, null=True)  # This field type is a guess.
#     administrative_expenses = models.TextField(blank=True, null=True)  # This field type is a guess.
#     total_outflow = models.TextField(blank=True, null=True)  # This field type is a guess.
#     pension_expense_gasb_67_68 = models.TextField(blank=True, null=True)  # This field type is a guess.
#     normal_cost_total = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     normal_cost_employer = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     normal_cost_employee = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     amortization_payment_total = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     amortization_payment_employer = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     amortization_payment_employee = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     health_care_premium = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     administrative_expenses_if_separated_from_normal_cost = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     db_employer_contribution_total = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     db_employee_contribution_total = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     db_multiplier_specified_or_range = models.CharField(max_length=100, blank=True, null=True)
#     dc_employer_rate = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     dc_employee_rate = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     cola_or_pbi_offered = models.CharField(max_length=100, blank=True, null=True)
#     cola_benefit = models.CharField(max_length=100, blank=True, null=True)
#     drop_available_for_new_hires = models.CharField(max_length=100, blank=True, null=True)
#     health_benefit_offered = models.NullBooleanField()
#     db_plan_associated_with_a_hybrid_dc = models.NullBooleanField()
#     db_plan_associated_with_optional_457_or_other_dc = models.NullBooleanField()
#     inflation_rate_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     interest_rate_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     payroll_growth_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     salary_wage_growth_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     separation_termination_rate_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     retirement_rate_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     mortality_table_year_adjustments = models.CharField(max_length=100, blank=True, null=True)
#     amortizaton_method = models.CharField(max_length=100, blank=True, null=True)
#     number_of_years_remaining_on_amortization_schedule = models.CharField(max_length=100, blank=True, null=True)
#     actuarial_cost_method_in_funding_policy = models.CharField(max_length=100, blank=True, null=True)
#     actuarial_cost_method_in_valuation = models.CharField(max_length=100, blank=True, null=True)
#     definition_of_disability = models.CharField(max_length=255, blank=True, null=True)
#     determiniation_of_disability = models.CharField(max_length=255, blank=True, null=True)
#     discount_rate_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     does_plan_apply_multiple_discount_rates = models.NullBooleanField()
#     single_discount_rate_gasb_67_68 = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     rate_of_return_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     number_of_years_used_for_smoothing_actuarial_return = models.IntegerField(blank=True, null=True)
#     actuarial_investment_return_ava_basis = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     market_investment_return_mva_basis = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     adjusted_market_investment_return_mva_basis = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     geometric_average_5yr_mva = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     geometric_average_10yr_mva = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     geometric_average_15yr_mva = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     commingling_type = models.CharField(max_length=100, blank=True, null=True)
#     total_percentage_of_investments_in_equities = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     total_percentage_of_investments_in_fixed_income = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
#     total_percentage_of_investments_in_real_estate = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)

#     class Meta:
#         managed = False
#         db_table = 'reason_data'

# class SleppData(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     plan_name = models.TextField()
#     state = models.TextField()
#     social_security_coverage = models.TextField()
#     source = models.TextField()

#     class Meta:
#         managed = False
#         db_table = 'slepp_data'






        

