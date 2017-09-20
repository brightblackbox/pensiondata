"""
Definition of models.
"""

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

#########################################################################################################

class CensusData(models.Model):
    id = models.BigAutoField(primary_key=True)
    state_contribution_for_local_employees = models.DecimalField(max_digits=10, decimal_places=6)

    class Meta:
        managed = False
        db_table = 'census_data'



class County(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    retirement_census_county_code = models.CharField(max_length=3)
    retirement_census_state_code = models.CharField(max_length=2)
    state = models.ForeignKey('State', models.DO_NOTHING, null=False)

    class Meta:
        db_table = 'county'

    def __str__(self):
        return self.name

class DataSource(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    trust_level = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'data_source'

    def __str__(self):
        return self.name

class Government(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    state = models.ForeignKey('State', models.DO_NOTHING, null=False)
    government_type = models.ForeignKey('GovernmentType', models.DO_NOTHING)
    county = models.ForeignKey(County, models.DO_NOTHING)

    class Meta:
        db_table = 'government'

    def __str__(self):
        return self.name

class GovernmentAnnual(models.Model):
    id = models.BigAutoField(primary_key=True)
    government = models.ForeignKey(Government, models.DO_NOTHING)
    government_attribute = models.ForeignKey('GovernmentAttribute', models.DO_NOTHING)
    attribute_value = models.TextField()

    class Meta:
        managed = False
        db_table = 'government_annual'

class GovernmentAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    attribute_key = models.TextField()
    attribute_datatype = models.IntegerField()
    attribute_category = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'government_attribute'

class GovernmentType(models.Model):
    id = models.BigAutoField(primary_key=True)
    level = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'government_type'

    def __str__(self):
        return self.level

class Plan(models.Model):
    id = models.BigAutoField(primary_key=True)
    census_plan_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    year_of_inception = models.IntegerField(blank=True, null=True)
    benefit_tier = models.IntegerField(blank=True, null=True)
    year_closed = models.IntegerField(blank=True, null=True)
    web_site = models.CharField(max_length=255, blank=True, null=True)
    admin_gov = models.ForeignKey(Government, models.DO_NOTHING, blank=True, null=False)
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
        managed = False
        db_table = 'plan'

    # @property
    # def gov_state(self):
    # #     # return 'CO'
    #     return State.objects.values_list('state_abbreviation').first()
    # #     # return 

class PlanAnnual(models.Model):
    id = models.BigAutoField(primary_key=True)
    plan = models.ForeignKey('Plan', models.DO_NOTHING)
    year = models.CharField(max_length=4)
    government_id = models.BigIntegerField()
    # census_plan_annual = models.OneToOneField('CensusPlanAnnualAttribute', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'plan_annual'

class PlanAnnualAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    plan_annual = models.ForeignKey('PlanAnnual', models.DO_NOTHING, null=False)
    plan = models.ForeignKey('Plan', models.DO_NOTHING, null=False)
    year = models.CharField(max_length=4)
    plan_attribute = models.ForeignKey('PlanAttribute', models.DO_NOTHING, null=False)
    attribute_value = models.CharField(max_length=256)

    class Meta:
        managed = False
        db_table = 'plan_annual_attribute'

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
    plan_attribute_category = models.ForeignKey('PlanAttributeCategory', models.DO_NOTHING, null=False)
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
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=256)
    datatype = models.CharField(max_length=256)
    plan_attribute_category = models.ForeignKey('PlanAttributeCategory', models.DO_NOTHING, null=False)
    line_item_code = models.CharField(max_length=256)
    display_order = models.IntegerField()
    attribute_column_name = models.CharField(max_length=256)
    multiplier = models.DecimalField(max_digits=30, decimal_places=6)
    weight = models.IntegerField()
    plan_attribute_master = models.ForeignKey('PlanAttributeMaster', models.DO_NOTHING, null=False)
    data_source = models.ForeignKey('DataSource', models.DO_NOTHING, null=False)

    class Meta:
        managed = True
        db_table = 'plan_attribute'

    def __str__(self):
        return self.name

### THIS MODEL IS A WORK IN PROGRESS -- DO NOT USE FOR NOW
class PlanInheritance(models.Model):
    id = models.BigAutoField(primary_key=True)
    parent_plan = models.ForeignKey('Plan', models.DO_NOTHING, related_name='parent_plan_fk')
    child_plan = models.ForeignKey('Plan', models.DO_NOTHING, related_name='child_plan_fk')
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

attrs = {
    'name': models.CharField(max_length=32),
    '__module__': 'pensiondata.models',
    '__app_label__': 'pensiondata'
}
CensusPlanAnnualAttribute = type("CensusPlanAnnualAttribute", (models.Model,), attrs)

# class CensusPlanAnnualAttribute(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     plan_annual = models.OneToOneField('PlanAnnual', models.DO_NOTHING)
#     data_source_id = models.BigIntegerField()
#     plan = models.ForeignKey('Plan', models.DO_NOTHING)
#     year = models.CharField(max_length=4)
#     contributions_by_state_employees = models.FloatField(blank=True, null=True)
#     contributions_by_local_employees = models.FloatField(blank=True, null=True)
#     total_employee_contributions = models.FloatField(blank=True, null=True)
#     state_contributions_on_behalf_of_state_employees = models.FloatField(blank=True, null=True)
#     state_contributions_on_behalf_of_local_employees = models.FloatField(blank=True, null=True)
#     local_government_contributions = models.FloatField(blank=True, null=True)
#     contributions_from_parent_local_governments = models.FloatField(blank=True, null=True)
#     interest_earnings = models.FloatField(blank=True, null=True)
#     dividend_earnings = models.FloatField(blank=True, null=True)
#     other_investment_earnings = models.FloatField(blank=True, null=True)
#     gains_on_investments = models.FloatField(blank=True, null=True)
#     losses_on_investments = models.FloatField(blank=True, null=True)
#     total_earnings_on_investments = models.FloatField(blank=True, null=True)
#     receipts_for_transmittal_to_federal_social_security_system = models.FloatField(blank=True, null=True)
#     rentals_from_state_government = models.FloatField(blank=True, null=True)
#     retirement_benefits = models.FloatField(blank=True, null=True)
#     disability_benefist = models.FloatField(blank=True, null=True)
#     survivor_benefits = models.FloatField(blank=True, null=True)
#     other_benefits = models.FloatField(blank=True, null=True)
#     total_benefit_payments = models.FloatField(blank=True, null=True)
#     withdrawals = models.FloatField(blank=True, null=True)
#     administrative_expenses = models.FloatField(blank=True, null=True)
#     time_or_savings_deposits = models.FloatField(blank=True, null=True)
#     cash_on_hand_and_demand_deposits = models.FloatField(blank=True, null=True)
#     all_other_short_term_investments = models.FloatField(blank=True, null=True)
#     total_cash_and_short_term_investments = models.FloatField(blank=True, null=True)
#     federal_agency_securities = models.FloatField(blank=True, null=True)
#     federal_treasury_securities = models.FloatField(blank=True, null=True)
#     federally_sponsored_agencies = models.FloatField(blank=True, null=True)
#     total_federal_government_securities = models.FloatField(blank=True, null=True)
#     corporate_bonds_other = models.FloatField(blank=True, null=True)
#     total_corporate_bonds = models.FloatField(blank=True, null=True)
#     mortgages_held_directly = models.FloatField(blank=True, null=True)
#     corporate_stocks = models.FloatField(blank=True, null=True)
#     investments_held_in_trust_by_other_agencies = models.FloatField(blank=True, null=True)
#     state_and_local_government_securities = models.FloatField(blank=True, null=True)
#     foreign_and_international_securities = models.FloatField(blank=True, null=True)
#     other_securities = models.FloatField(blank=True, null=True)
#     total_other_investments = models.FloatField(blank=True, null=True)
#     real_property = models.FloatField(blank=True, null=True)
#     other_investments = models.FloatField(blank=True, null=True)
#     total_cash_and_securities = models.FloatField(blank=True, null=True)
#     actuarially_accured_liabilities = models.FloatField(blank=True, null=True)
#     state_government_active_members = models.FloatField(blank=True, null=True)
#     local_government_active_members = models.FloatField(blank=True, null=True)
#     total_active_members = models.FloatField(blank=True, null=True)
#     inactive_members = models.FloatField(blank=True, null=True)
#     former_active_members_retired_on_account_of_age_or_service = models.FloatField(blank=True, null=True)
#     former_active_members_retired_on_account_of_disability = models.FloatField(blank=True, null=True)
#     survivors = models.FloatField(blank=True, null=True)
#     covered_payroll = models.FloatField(blank=True, null=True)

#     class Meta:
#         managed = False
#         db_table = 'census_plan_annual_attribute'

# class PPDPlanAnnualAttribute(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     plan_annual = models.OneToOneField('PlanAnnual', models.DO_NOTHING)
#     plan = models.ForeignKey('Plan', models.DO_NOTHING)
#     year = models.CharField(max_length=4, blank=True, null=True)
#     ppd_id = models.BigIntegerField(blank=True, null=True)
#     planname = models.CharField(max_length=256, blank=True, null=True)
#     fy = models.CharField(max_length=4, blank=True, null=True)
#     system_id = models.BigIntegerField(blank=True, null=True)
#     valuationid = models.BigIntegerField(blank=True, null=True)
#     planfullname = models.CharField(max_length=256, blank=True, null=True)
#     source_planbasics = models.CharField(max_length=256, blank=True, null=True)
#     inpfs = models.BigIntegerField(blank=True, null=True)
#     fiscalyeartype = models.BigIntegerField(blank=True, null=True)
#     planinceptionyear = models.CharField(max_length=256, blank=True, null=True)
#     planclosed = models.BigIntegerField(blank=True, null=True)
#     planyearclosed = models.CharField(max_length=4, blank=True, null=True)
#     administeringgovt = models.BigIntegerField(blank=True, null=True)
#     stateabbrev = models.CharField(max_length=256, blank=True, null=True)
#     statename = models.CharField(max_length=256, blank=True, null=True)
#     govtname = models.CharField(max_length=256, blank=True, null=True)
#     plantype = models.BigIntegerField(blank=True, null=True)
#     employeetypecovered = models.CharField(max_length=256, blank=True, null=True)
#     socseccovered = models.BigIntegerField(blank=True, null=True)
#     socseccovered_verbatim = models.CharField(max_length=256, blank=True, null=True)
#     coststructure = models.CharField(max_length=256, blank=True, null=True)
#     employertype = models.BigIntegerField(blank=True, null=True)
#     costsharing = models.BigIntegerField(blank=True, null=True)
#     stateemployers = models.BigIntegerField(blank=True, null=True)
#     localemployers = models.BigIntegerField(blank=True, null=True)
#     schoolemployers = models.BigIntegerField(blank=True, null=True)
#     coversstateemployees = models.BigIntegerField(blank=True, null=True)
#     coverslocalemployees = models.BigIntegerField(blank=True, null=True)
#     coversteachers = models.BigIntegerField(blank=True, null=True)
#     stategenee = models.BigIntegerField(blank=True, null=True)
#     localgenee = models.BigIntegerField(blank=True, null=True)
#     statepolice = models.BigIntegerField(blank=True, null=True)
#     localpolice = models.BigIntegerField(blank=True, null=True)
#     statefire = models.BigIntegerField(blank=True, null=True)
#     localfire = models.BigIntegerField(blank=True, null=True)
#     teacher = models.BigIntegerField(blank=True, null=True)
#     schoolees = models.BigIntegerField(blank=True, null=True)
#     judgesattorneys = models.BigIntegerField(blank=True, null=True)
#     electedofficials = models.BigIntegerField(blank=True, null=True)
#     benefitswebsite = models.CharField(max_length=256, blank=True, null=True)
#     reportingdatenotes = models.CharField(max_length=256, blank=True, null=True)
#     eegroupid = models.BigIntegerField(blank=True, null=True)
#     tierid = models.BigIntegerField(blank=True, null=True)
#     cafr_cy = models.BigIntegerField(blank=True, null=True)
#     actrpt_cy = models.BigIntegerField(blank=True, null=True)
#     cafr_av_conflict = models.BigIntegerField(blank=True, null=True)
#     actrptdate = models.DateField(blank=True, null=True)
#     fye = models.DateField(blank=True, null=True)
#     dataentrycode = models.CharField(max_length=256, blank=True, null=True)
#     source_gasbassumptions = models.CharField(max_length=256, blank=True, null=True)
#     actcostmeth_gasb = models.CharField(max_length=256, blank=True, null=True)
#     assetvalmeth_gasb = models.CharField(max_length=256, blank=True, null=True)
#     fundingmeth_gasb = models.CharField(max_length=256, blank=True, null=True)
#     cola_verabatim = models.CharField(max_length=256, blank=True, null=True)
#     cola_code = models.CharField(max_length=256, blank=True, null=True)
#     inflationassumption_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturnassumption_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actcostmethcode_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     assetvalmethcode_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     assetsmoothingperiod_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     fundingmethcode1_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     fundingmethcode2_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     uaalamortperiod_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     blendeddiscountrate = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actvaldate_gasbassumptions = models.DateField(blank=True, null=True)
#     source_fundingandmethods = models.CharField(max_length=256, blank=True, null=True)
#     assetvalmeth = models.CharField(max_length=256, blank=True, null=True)
#     phasein = models.CharField(max_length=256, blank=True, null=True)
#     assetvalmeth_note = models.CharField(max_length=256, blank=True, null=True)
#     actcostmeth = models.CharField(max_length=256, blank=True, null=True)
#     actcostmeth_note = models.CharField(max_length=256, blank=True, null=True)
#     fundingmeth = models.CharField(max_length=256, blank=True, null=True)
#     fundingmeth_note = models.CharField(max_length=256, blank=True, null=True)
#     mktassets_smooth = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actassets_smooth = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     netflows_smooth = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     assetvalmethcode = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     smoothingreset = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     gainlossconcept = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     gainlossbase_1 = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     gainlossbase_2 = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     gainloss = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     gainlossperiod = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     phaseinpercent = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     phaseinperiods = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     phaseintype = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     gainlossrecognition = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     assetsmoothingbaseline = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expectedreturnmethod = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     addsubtractgainloss = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     uppercorridor = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     lowercorridor = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actcostmethcode = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     fundmethcode_1 = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     fundmethcode_2 = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     payrollgrowthassumption = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     totamortperiod = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     remainingamortperiod = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     uaalyearestablished = models.CharField(max_length=4, blank=True, null=True)
#     wageinflation = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     source_gasbschedules = models.CharField(max_length=256, blank=True, null=True)
#     aj = models.CharField(max_length=256, blank=True, null=True)
#     ak = models.CharField(max_length=256, blank=True, null=True)
#     actassets_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actliabilities_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actfundedratio_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     uaal_gasb = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actliabilities_other = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     payroll = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     requiredcontribution = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     percentreqcontpaid = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     arc = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     percentarcpaid = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     totalpensionliability = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     netposition = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     netpensionliability = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     adec = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     aec = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     coveredpayroll_gasb67 = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     percentadec = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actassets_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actliabilities_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actfundedratio_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     requiredcontribution_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actfundedratio_gasb67 = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actvaldate_gasbschedules = models.DateField(blank=True, null=True)
#     source_investmentreturn = models.CharField(max_length=256, blank=True, null=True)
#     investmentreturn_1yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_2yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_3yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_4yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_5yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_7yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_8yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_10yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_12yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_15yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_20yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_25yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_30yr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_longterm = models.CharField(max_length=256, blank=True, null=True)
#     investmentreturn_longtermstartye = models.CharField(max_length=256, blank=True, null=True)
#     grossreturns = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     georeturn_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     geogrowth_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_1yr_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_5yr_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     investmentreturn_10yr_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     source_assetallocation = models.CharField(max_length=256, blank=True, null=True)
#     equities_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     equities_domestic = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     equities_international = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     fixedincome_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     fixedincome_domestic = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     fixedincome_international = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     realestate = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     cashandshortterm = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     alternatives = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     other = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     source_incomestatement = models.CharField(max_length=256, blank=True, null=True)
#     fairvaluechange_seclend = models.CharField(max_length=256, blank=True, null=True)
#     expense_seclendmgmtfees = models.CharField(max_length=256, blank=True, null=True)
#     fairvaluechange_seclendug = models.CharField(max_length=256, blank=True, null=True)
#     contrib_ee_regular = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     contrib_er_regular = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     contrib_er_state = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     contrib_ee_purchaseservice = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     contrib_ee_other = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     contrib_er_other = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     contrib_other = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     contrib_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     fairvaluechange_investments = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     fairvaluechange_realestate = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_interest = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_dividends = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_interestanddividends = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_realestate = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_privateequity = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_alternatives = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_international = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_otherinvestments = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_realestate = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_privateequity = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_alternatives = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_otherinvestments = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_investments = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_securitieslending = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_securitieslending = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_securitieslendingrebate = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_otheradditions = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     income_net = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_totbenefits = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_retbenefits = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_disabilitybenefits = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_deathbenefits = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_dropbenefits = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_survivorbenefits = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_colabenefits = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_lumpsumbenefits = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_otherbenefits = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_refunds = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_adminexpenses = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_depreciation = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_otherdeductions = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     expense_net = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     adjustment_mktassets = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     mktassets_net = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     source_actcosts = models.CharField(max_length=256, blank=True, null=True)
#     contributionfy = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     normcostrate_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     normcostrate_ee = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     normcostrate_er = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     reqcontrate_er = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     reqcontrate_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     normcostamount_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     normcostamount_ee = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     normcostamount_er = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     reqcontamount_er = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     reqcontamount_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     normcostrate_tot_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     normcostrate_ee_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     normcostrate_er_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     reqcontrate_er_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     projectedpayroll = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actvaldate_actuarialcosts = models.CharField(max_length=256, blank=True, null=True)
#     uaalrate = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     source_membership = models.CharField(max_length=256, blank=True, null=True)
#     beneficiaries_disabilityretirees = models.CharField(max_length=256, blank=True, null=True)
#     beneficiaries_dependentsurvivors = models.CharField(max_length=256, blank=True, null=True)
#     actives_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     activesalaries = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     activeage_avg = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     activetenure_avg = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     activesalary_avg = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     inactivevestedmembers = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     inactivenonvested = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     beneficiaries_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     benefits_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     beneficiaryage_avg = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     beneficiarybenefit_avg = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     beneficiaries_serviceretirees = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     benefits_serviceretirees = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     serviceretireeage_avg = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     serviceretireebenefit_avg = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     serviceretage_avg = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     servicerettenure_avg = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     serviceretbenefit_avg = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     benefits_disabilityretirees = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     beneficiaries_survivors = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     beneficiaries_spousalsurvivors = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     beneficiaries_other = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     dropmembers = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     othermembers = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     totmembership = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     activesalary_avg_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     beneficiarybenefit_avg_est = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     source_actliabilities = models.CharField(max_length=256, blank=True, null=True)
#     pvfb_inactivenonvested = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     pvfb_active = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     pvfb_inactivevested = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     pvfb_retiree = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     pvfb_other = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     pvfb_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     pvfnc_tot = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     pvfnc_ee = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     pvfnc_er = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     pvfs = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     mktassets_actrpt = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actassets_ava = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actliabilities_ean = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     actliabilities_puc = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     nocafr = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     noav = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
#     planleveldata = models.BigIntegerField(blank=True, null=True)

#     class Meta:
#         managed = False
#         db_table = 'ppd_plan_annual_attribute'

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






        