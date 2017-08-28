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

class CensusPlanAnnualAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    plan_annual = models.OneToOneField('PlanAnnual', models.DO_NOTHING)
    data_source_id = models.BigIntegerField()
    plan_id = models.BigIntegerField()
    year = models.CharField(max_length=4)
    contributions_by_state_employees = models.FloatField(blank=True, null=True)
    contributions_by_local_employees = models.FloatField(blank=True, null=True)
    total_employee_contributions = models.FloatField(blank=True, null=True)
    state_contributions_on_behalf_of_state_employees = models.FloatField(blank=True, null=True)
    state_contributions_on_behalf_of_local_employees = models.FloatField(blank=True, null=True)
    local_government_contributions = models.FloatField(blank=True, null=True)
    contributions_from_parent_local_governments = models.FloatField(blank=True, null=True)
    interest_earnings = models.FloatField(blank=True, null=True)
    dividend_earnings = models.FloatField(blank=True, null=True)
    other_investment_earnings = models.FloatField(blank=True, null=True)
    gains_on_investments = models.FloatField(blank=True, null=True)
    losses_on_investments = models.FloatField(blank=True, null=True)
    total_earnings_on_investments = models.FloatField(blank=True, null=True)
    receipts_for_transmittal_to_federal_social_security_system = models.FloatField(blank=True, null=True)
    rentals_from_state_government = models.FloatField(blank=True, null=True)
    retirement_benefits = models.FloatField(blank=True, null=True)
    disability_benefist = models.FloatField(blank=True, null=True)
    survivor_benefits = models.FloatField(blank=True, null=True)
    other_benefits = models.FloatField(blank=True, null=True)
    total_benefit_payments = models.FloatField(blank=True, null=True)
    withdrawals = models.FloatField(blank=True, null=True)
    administrative_expenses = models.FloatField(blank=True, null=True)
    time_or_savings_deposits = models.FloatField(blank=True, null=True)
    cash_on_hand_and_demand_deposits = models.FloatField(blank=True, null=True)
    all_other_short_term_investments = models.FloatField(blank=True, null=True)
    total_cash_and_short_term_investments = models.FloatField(blank=True, null=True)
    federal_agency_securities = models.FloatField(blank=True, null=True)
    federal_treasury_securities = models.FloatField(blank=True, null=True)
    federally_sponsored_agencies = models.FloatField(blank=True, null=True)
    total_federal_government_securities = models.FloatField(blank=True, null=True)
    corporate_bonds_other = models.FloatField(blank=True, null=True)
    total_corporate_bonds = models.FloatField(blank=True, null=True)
    mortgages_held_directly = models.FloatField(blank=True, null=True)
    corporate_stocks = models.FloatField(blank=True, null=True)
    investments_held_in_trust_by_other_agencies = models.FloatField(blank=True, null=True)
    state_and_local_government_securities = models.FloatField(blank=True, null=True)
    foreign_and_international_securities = models.FloatField(blank=True, null=True)
    other_securities = models.FloatField(blank=True, null=True)
    total_other_investments = models.FloatField(blank=True, null=True)
    real_property = models.FloatField(blank=True, null=True)
    other_investments = models.FloatField(blank=True, null=True)
    total_cash_and_securities = models.FloatField(blank=True, null=True)
    actuarially_accured_liabilities = models.FloatField(blank=True, null=True)
    state_government_active_members = models.FloatField(blank=True, null=True)
    local_government_active_members = models.FloatField(blank=True, null=True)
    total_active_members = models.FloatField(blank=True, null=True)
    inactive_members = models.FloatField(blank=True, null=True)
    former_active_members_retired_on_account_of_age_or_service = models.FloatField(blank=True, null=True)
    former_active_members_retired_on_account_of_disability = models.FloatField(blank=True, null=True)
    survivors = models.FloatField(blank=True, null=True)
    covered_payroll = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'census_plan_annual_attribute'

class County(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    county_fips_code = models.CharField(max_length=3)
    state_fips_code = models.CharField(max_length=2)
    fips_class_code = models.CharField(max_length=2)

    class Meta:
        managed = False
        db_table = 'county'

class Government(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    state = models.ForeignKey('State', models.DO_NOTHING)
    government_type = models.ForeignKey('GovernmentType', models.DO_NOTHING)
    county = models.ForeignKey(County, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'government'

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

class Plan(models.Model):
    id = models.BigAutoField(primary_key=True)
    census_plan_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
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
        managed = False
        db_table = 'plan'

class PlanAnnual(models.Model):
    id = models.BigAutoField(primary_key=True)
    plan = models.ForeignKey('Plan', models.DO_NOTHING)
    year = models.CharField(max_length=4)
    government_id = models.BigIntegerField()
    # census_plan_annual = models.OneToOneField('CensusPlanAnnualAttribute', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'plan_annual'

class PlanAnnualAttributes(models.Model):
    id = models.BigAutoField(primary_key=True)
    plan = models.ForeignKey(Plan, models.DO_NOTHING)
    plan_attribute = models.ForeignKey('PlanAttribute', models.DO_NOTHING)
    attribute_value = models.TextField()

    class Meta:
        managed = False
        db_table = 'plan_annual_attributes'

class PlanAttribute(models.Model):
    id = models.BigAutoField(primary_key=True)
    attribute = models.TextField()
    datatype = models.TextField()
    category = models.TextField()
    line_item_code = models.TextField()

    class Meta:
        managed = False
        db_table = 'plan_attribute'

class PlanInheritance(models.Model):
    id = models.BigAutoField(primary_key=True)
    parent_plan = models.ForeignKey(Plan, models.DO_NOTHING, related_name='parent_plan_fk')
    child_plan = models.ForeignKey(Plan, models.DO_NOTHING, related_name='child_plan_fk')
    level = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'plan_inheritance'

class PlanProvisions(models.Model):
    id = models.ForeignKey(Plan, models.DO_NOTHING, db_column='id', primary_key=True)
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

class ReasonData(models.Model):
    id = models.BigAutoField(primary_key=True)
    fiscal_year = models.IntegerField()
    fiscal_year_end_date = models.DateField()
    adec = models.TextField(blank=True, null=True)  # This field type is a guess.
    adec_paid = models.TextField(blank=True, null=True)  # This field type is a guess.
    adec_missed = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    percent_of_adec_paid = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    fiduciary_net_position_or_mva = models.TextField(blank=True, null=True)  # This field type is a guess.
    total_pension_liability_or_aal = models.TextField(blank=True, null=True)  # This field type is a guess.
    net_pension_liability_or_ual = models.TextField(blank=True, null=True)  # This field type is a guess.
    funded_ratio_gasb_67_68 = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    net_pension_liability_using_rate_minus_1 = models.TextField(blank=True, null=True)  # This field type is a guess.
    net_pension_liability_using_rate_plus_1 = models.TextField(blank=True, null=True)  # This field type is a guess.
    actuarially_required_contribution = models.TextField(blank=True, null=True)  # This field type is a guess.
    total_arc_paid = models.TextField(blank=True, null=True)  # This field type is a guess.
    total_arc_missed = models.TextField(blank=True, null=True)  # This field type is a guess.
    percent_of_arc_paid = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    actuarial_value_of_assets = models.TextField(blank=True, null=True)  # This field type is a guess.
    actuarial_acrrued_liability = models.TextField(blank=True, null=True)  # This field type is a guess.
    unfunded_accrued_liability = models.TextField(blank=True, null=True)  # This field type is a guess.
    funded_ratio_gasb_25 = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    covered_payroll = models.TextField(blank=True, null=True)  # This field type is a guess.
    adec_as_a_percent_of_payroll = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    arc_as_a_percent_of_payroll = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    market_value_of_assets = models.TextField(blank=True, null=True)  # This field type is a guess.
    market_value_funded_ratio = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    total_actuarial_gain_loss = models.TextField(blank=True, null=True)  # This field type is a guess.
    benefit_payments = models.TextField(blank=True, null=True)  # This field type is a guess.
    refunds = models.TextField(blank=True, null=True)  # This field type is a guess.
    administrative_expenses = models.TextField(blank=True, null=True)  # This field type is a guess.
    total_outflow = models.TextField(blank=True, null=True)  # This field type is a guess.
    pension_expense_gasb_67_68 = models.TextField(blank=True, null=True)  # This field type is a guess.
    normal_cost_total = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    normal_cost_employer = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    normal_cost_employee = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    amortization_payment_total = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    amortization_payment_employer = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    amortization_payment_employee = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    health_care_premium = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    administrative_expenses_if_separated_from_normal_cost = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    db_employer_contribution_total = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    db_employee_contribution_total = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    db_multiplier_specified_or_range = models.CharField(max_length=100, blank=True, null=True)
    dc_employer_rate = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    dc_employee_rate = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    cola_or_pbi_offered = models.CharField(max_length=100, blank=True, null=True)
    cola_benefit = models.CharField(max_length=100, blank=True, null=True)
    drop_available_for_new_hires = models.CharField(max_length=100, blank=True, null=True)
    health_benefit_offered = models.NullBooleanField()
    db_plan_associated_with_a_hybrid_dc = models.NullBooleanField()
    db_plan_associated_with_optional_457_or_other_dc = models.NullBooleanField()
    inflation_rate_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    interest_rate_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    payroll_growth_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    salary_wage_growth_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    separation_termination_rate_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    retirement_rate_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    mortality_table_year_adjustments = models.CharField(max_length=100, blank=True, null=True)
    amortizaton_method = models.CharField(max_length=100, blank=True, null=True)
    number_of_years_remaining_on_amortization_schedule = models.CharField(max_length=100, blank=True, null=True)
    actuarial_cost_method_in_funding_policy = models.CharField(max_length=100, blank=True, null=True)
    actuarial_cost_method_in_valuation = models.CharField(max_length=100, blank=True, null=True)
    definition_of_disability = models.CharField(max_length=255, blank=True, null=True)
    determiniation_of_disability = models.CharField(max_length=255, blank=True, null=True)
    discount_rate_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    does_plan_apply_multiple_discount_rates = models.NullBooleanField()
    single_discount_rate_gasb_67_68 = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    rate_of_return_assumption = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    number_of_years_used_for_smoothing_actuarial_return = models.IntegerField(blank=True, null=True)
    actuarial_investment_return_ava_basis = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    market_investment_return_mva_basis = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    adjusted_market_investment_return_mva_basis = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    geometric_average_5yr_mva = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    geometric_average_10yr_mva = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    geometric_average_15yr_mva = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    commingling_type = models.CharField(max_length=100, blank=True, null=True)
    total_percentage_of_investments_in_equities = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    total_percentage_of_investments_in_fixed_income = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    total_percentage_of_investments_in_real_estate = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reason_data'

class SleppData(models.Model):
    id = models.BigAutoField(primary_key=True)
    plan_name = models.TextField()
    state = models.TextField()
    social_security_coverage = models.TextField()
    source = models.TextField()

    class Meta:
        managed = False
        db_table = 'slepp_data'

class State(models.Model):
    id = models.BigAutoField(primary_key=True)
    state_fips_code = models.CharField(max_length=2)
    name = models.TextField()
    abbreviation = models.CharField(max_length=2)

    class Meta:
        managed = False
        db_table = 'state'




        