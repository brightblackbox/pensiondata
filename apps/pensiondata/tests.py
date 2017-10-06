from django.core.urlresolvers import reverse

from .utils import BaseTestCase as TestCase
from .models import PlanAnnualAttribute


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

