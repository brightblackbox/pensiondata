from django.core.urlresolvers import reverse
import json

from .utils import BaseTestCase as TestCase
from .models import PlanAnnualAttribute, PlanAttribute


class PensionTest(TestCase):
    def setUp(self):
        self.create_init_data()

    def test_del_planannualattr(self):
        print('Delete test---------------')
        self.login_admin()
        url = reverse('pensiondata:delete_plan_annual_attr')

        # ajax post
        response = self.client.post(url, {'attr_id': self.plan_annual_attr.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(PlanAnnualAttribute.objects.filter(id=self.plan_annual_attr.pk).exists())

    def test_read_calc_rule(self):
        print('Readable function test---------------')
        self.assertEqual(
            self.plan_calculated_attr.get_rule_readable(), 'test-static-attr1*100-(200/3)+test-static-attr2'
        )

    def test_value_with_calc_rule(self):
        print('Value function test---------------')
        calc_value = float(self.plan_annual_attr_with_calc_rule.value)
        static_value1 = int(self.plan_annual_attr_with_static1.attribute_value)
        static_value2 = int(self.plan_annual_attr_with_static2.attribute_value)

        self.assertEqual(
            calc_value,
            static_value1*100-(200/3)+static_value2
        )

    def test_edit_planannualattr(self):
        print('Edit test---------------')
        self.login_admin()
        url = reverse('pensiondata:edit_plan_annual_attr')

        # ajax post
        # plan_annual_attr_with_static2 old_val = 222
        response = self.client.post(url, {'attr_id': self.plan_annual_attr_with_static2.id, 'new_val': '2'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # print('Response: {}'.format(response.__dict__))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlanAnnualAttribute.objects.get(id=self.plan_annual_attr_with_static2.id).attribute_value,
                         '2')

        # check signal
        static_value1 = 111
        static_value2 = 2
        self.assertEqual(PlanAnnualAttribute.objects.get(id=self.plan_annual_attr_with_calc_rule.id).attribute_value,
                         str(static_value1*100-(200/3)+static_value2))

    def test_add_planannualattr(self):
        print('Add test---------------')
        self.login_admin()
        url = reverse('pensiondata:add_plan_annual_attr')

        # already exists
        response = self.client.post(url, {'attr_id': self.plan_static_attr1.id,
                                          'plan_id': self.plan.id,
                                          'year': '2017',
                                          'value': '2'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(response['result'], 'fail')

        # add new obj with static attr
        response = self.client.post(url, {'attr_id': self.plan_static_attr1.id,
                                          'plan_id': self.plan.id,
                                          'year': '2016',
                                          'value': '2'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(response['result'], 'success')
        self.assertTrue(PlanAnnualAttribute.objects.filter(plan=self.plan, year='2016', plan_attribute=self.plan_static_attr1).exists())
