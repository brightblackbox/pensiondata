from django.core.urlresolvers import reverse

from .utils import BaseTestCase as TestCase
from .models import PlanAnnualAttribute, PlanAttribute


class PensionTest(TestCase):
    def setUp(self):
        self.create_init_data()

    def test_del_planannualattr(self):
        self.login_admin()
        url = reverse('pensiondata:delete_plan_attr')

        # ajax post
        response = self.client.post(url, {'attr_id': self.plan_annual_attr.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(PlanAnnualAttribute.objects.filter(id=self.plan_annual_attr.pk).exists())

    def test_read_calc_rule(self):

        self.assertEqual(
            self.plan_calculated_attr.get_rule_readable(), 'test-static-attr1*100-(200/3)+test-static-attr2'
        )

    def test_value_with_calc_rule(self):
        calc_value = float(self.plan_annual_attr_with_calc_rule.value)
        static_value1 = int(self.plan_annual_attr_with_static1.value)
        static_value2 = int(self.plan_annual_attr_with_static2.value)

        self.assertEqual(
            calc_value,
            static_value1*100-(200/3)+static_value2
        )
