# -*- coding: utf-8 -*-
import random
from django.contrib.auth.models import User
from django.test import TestCase

from .models import Plan, PlanAnnualAttribute, PlanAttribute, PlanAttributeCategory, DataSource, \
    State, Government


class BaseTestCase(TestCase):

    def create_init_data(self):
        self.admin = User.objects.create_user(username='admin', email='admin@test.com', password='test', is_staff=True)

        self.state = State.objects.create(name="test-state", state_abbreviation="xxx", retirement_census_state_code="xxx")
        self.govenment = Government.objects.create(name="test-goven", state=self.state)
        self.data_source = DataSource.objects.create(name="test-source", trust_level=1)
        self.category = PlanAttributeCategory.objects.create(name="test-category")
        self.plan = Plan.objects.create(census_plan_id=1, name="test-plan", admin_gov=self.govenment)
        self.plan_attr = PlanAttribute.objects.create(name="test-attr", plan_attribute_category=self.category, data_source=self.data_source)
        self.plan_annual_attr = PlanAnnualAttribute.objects.create(plan=self.plan, year="2017", plan_attribute=self.plan_attr, attribute_value="111")

    def login_admin(self):
        self.client.login(username=self.admin.username, password='test')
        self.session = self.client.session
        self.session.save()
