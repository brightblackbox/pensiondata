# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-23 07:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CensusData',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('state_contribution_for_local_employees', models.DecimalField(decimal_places=6, max_digits=10)),
            ],
            options={
                'db_table': 'census_data',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='County',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('county_fips_code', models.CharField(max_length=3)),
                ('state_fips_code', models.CharField(max_length=2)),
                ('fips_class_code', models.CharField(max_length=2)),
            ],
            options={
                'db_table': 'county',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Government',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'government',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='GovernmentAnnual',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('attribute_value', models.TextField()),
            ],
            options={
                'db_table': 'government_annual',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='GovernmentAttribute',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('attribute_key', models.TextField()),
                ('attribute_datatype', models.IntegerField()),
                ('attribute_category', models.IntegerField()),
            ],
            options={
                'db_table': 'government_attribute',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='GovernmentType',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('level', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'government_type',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('census_plan_id', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('year_of_inception', models.IntegerField(blank=True, null=True)),
                ('benefit_tier', models.IntegerField(blank=True, null=True)),
                ('year_closed', models.IntegerField(blank=True, null=True)),
                ('web_site', models.CharField(blank=True, max_length=255, null=True)),
                ('soc_sec_coverage', models.NullBooleanField()),
                ('soc_sec_coverage_notes', models.CharField(blank=True, max_length=255, null=True)),
                ('includes_state_employees', models.NullBooleanField()),
                ('includes_local_employees', models.NullBooleanField()),
                ('includes_safety_employees', models.NullBooleanField()),
                ('includes_general_employees', models.NullBooleanField()),
                ('includes_teachers', models.NullBooleanField()),
                ('intra_period_data_entity_id', models.BigIntegerField(blank=True, null=True)),
                ('intra_period_data_period_end_date', models.DateField(blank=True, null=True)),
                ('intra_period_data_period_type', models.IntegerField(blank=True, null=True)),
                ('gasb_68_type', models.CharField(blank=True, max_length=30, null=True)),
                ('state_gov_role', models.CharField(blank=True, max_length=30, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'plan',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PlanAnnual',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('year', models.CharField(max_length=4)),
            ],
            options={
                'db_table': 'plan_annual',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PlanAnnualAttributes',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('attribute_value', models.TextField()),
            ],
            options={
                'db_table': 'plan_annual_attributes',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PlanAttribute',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('attribute', models.TextField()),
                ('datatype', models.TextField()),
                ('category', models.TextField()),
                ('line_item_code', models.TextField()),
            ],
            options={
                'db_table': 'plan_attribute',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PlanInheritance',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('level', models.IntegerField()),
            ],
            options={
                'db_table': 'plan_inheritance',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ReasonData',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('fiscal_year', models.IntegerField()),
                ('fiscal_year_end_date', models.DateField()),
                ('adec', models.TextField(blank=True, null=True)),
                ('adec_paid', models.TextField(blank=True, null=True)),
                ('adec_missed', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('percent_of_adec_paid', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('fiduciary_net_position_or_mva', models.TextField(blank=True, null=True)),
                ('total_pension_liability_or_aal', models.TextField(blank=True, null=True)),
                ('net_pension_liability_or_ual', models.TextField(blank=True, null=True)),
                ('funded_ratio_gasb_67_68', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('net_pension_liability_using_rate_minus_1', models.TextField(blank=True, null=True)),
                ('net_pension_liability_using_rate_plus_1', models.TextField(blank=True, null=True)),
                ('actuarially_required_contribution', models.TextField(blank=True, null=True)),
                ('total_arc_paid', models.TextField(blank=True, null=True)),
                ('total_arc_missed', models.TextField(blank=True, null=True)),
                ('percent_of_arc_paid', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('actuarial_value_of_assets', models.TextField(blank=True, null=True)),
                ('actuarial_acrrued_liability', models.TextField(blank=True, null=True)),
                ('unfunded_accrued_liability', models.TextField(blank=True, null=True)),
                ('funded_ratio_gasb_25', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('covered_payroll', models.TextField(blank=True, null=True)),
                ('adec_as_a_percent_of_payroll', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('arc_as_a_percent_of_payroll', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('market_value_of_assets', models.TextField(blank=True, null=True)),
                ('market_value_funded_ratio', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('total_actuarial_gain_loss', models.TextField(blank=True, null=True)),
                ('benefit_payments', models.TextField(blank=True, null=True)),
                ('refunds', models.TextField(blank=True, null=True)),
                ('administrative_expenses', models.TextField(blank=True, null=True)),
                ('total_outflow', models.TextField(blank=True, null=True)),
                ('pension_expense_gasb_67_68', models.TextField(blank=True, null=True)),
                ('normal_cost_total', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('normal_cost_employer', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('normal_cost_employee', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('amortization_payment_total', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('amortization_payment_employer', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('amortization_payment_employee', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('health_care_premium', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('administrative_expenses_if_separated_from_normal_cost', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('db_employer_contribution_total', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('db_employee_contribution_total', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('db_multiplier_specified_or_range', models.CharField(blank=True, max_length=100, null=True)),
                ('dc_employer_rate', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('dc_employee_rate', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('cola_or_pbi_offered', models.CharField(blank=True, max_length=100, null=True)),
                ('cola_benefit', models.CharField(blank=True, max_length=100, null=True)),
                ('drop_available_for_new_hires', models.CharField(blank=True, max_length=100, null=True)),
                ('health_benefit_offered', models.NullBooleanField()),
                ('db_plan_associated_with_a_hybrid_dc', models.NullBooleanField()),
                ('db_plan_associated_with_optional_457_or_other_dc', models.NullBooleanField()),
                ('inflation_rate_assumption', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('interest_rate_assumption', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('payroll_growth_assumption', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('salary_wage_growth_assumption', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('separation_termination_rate_assumption', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('retirement_rate_assumption', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('mortality_table_year_adjustments', models.CharField(blank=True, max_length=100, null=True)),
                ('amortizaton_method', models.CharField(blank=True, max_length=100, null=True)),
                ('number_of_years_remaining_on_amortization_schedule', models.CharField(blank=True, max_length=100, null=True)),
                ('actuarial_cost_method_in_funding_policy', models.CharField(blank=True, max_length=100, null=True)),
                ('actuarial_cost_method_in_valuation', models.CharField(blank=True, max_length=100, null=True)),
                ('definition_of_disability', models.CharField(blank=True, max_length=255, null=True)),
                ('determiniation_of_disability', models.CharField(blank=True, max_length=255, null=True)),
                ('discount_rate_assumption', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('does_plan_apply_multiple_discount_rates', models.NullBooleanField()),
                ('single_discount_rate_gasb_67_68', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('rate_of_return_assumption', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('number_of_years_used_for_smoothing_actuarial_return', models.IntegerField(blank=True, null=True)),
                ('actuarial_investment_return_ava_basis', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('market_investment_return_mva_basis', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('adjusted_market_investment_return_mva_basis', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('geometric_average_5yr_mva', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('geometric_average_10yr_mva', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('geometric_average_15yr_mva', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('commingling_type', models.CharField(blank=True, max_length=100, null=True)),
                ('total_percentage_of_investments_in_equities', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('total_percentage_of_investments_in_fixed_income', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                ('total_percentage_of_investments_in_real_estate', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
            ],
            options={
                'db_table': 'reason_data',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='SleppData',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('plan_name', models.TextField()),
                ('state', models.TextField()),
                ('social_security_coverage', models.TextField()),
                ('source', models.TextField()),
            ],
            options={
                'db_table': 'slepp_data',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('state_fips_code', models.CharField(max_length=2)),
                ('name', models.TextField()),
                ('abbreviation', models.CharField(max_length=2)),
            ],
            options={
                'db_table': 'state',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PlanProvisions',
            fields=[
                ('id', models.ForeignKey(db_column='id', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='pensiondata.Plan')),
                ('effective_date', models.DateField()),
                ('sunset_date', models.DateField(blank=True, null=True)),
                ('vesting_period', models.IntegerField(blank=True, null=True)),
                ('early_retirement_age', models.IntegerField(blank=True, null=True)),
                ('normal_retirement_age', models.IntegerField(blank=True, null=True)),
                ('benefit_formula', models.CharField(blank=True, max_length=30, null=True)),
                ('final_average_salary', models.CharField(blank=True, max_length=100, null=True)),
                ('multiplier', models.CharField(blank=True, max_length=100, null=True)),
                ('benefit_supplement', models.CharField(blank=True, max_length=100, null=True)),
                ('early_retirement_penalty', models.CharField(blank=True, max_length=100, null=True)),
                ('early_retirement_formula', models.CharField(blank=True, max_length=100, null=True)),
                ('cost_of_living_adjustment', models.CharField(blank=True, max_length=100, null=True)),
                ('deferred_vested_start_date', models.CharField(blank=True, max_length=100, null=True)),
                ('mandatory_retirement', models.NullBooleanField()),
                ('deferred_retirement_option_program', models.NullBooleanField()),
            ],
            options={
                'db_table': 'plan_provisions',
                'managed': False,
            },
        ),
    ]
