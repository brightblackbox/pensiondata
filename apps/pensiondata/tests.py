from django.core.urlresolvers import reverse
import json

from .utils import BaseTestCase as TestCase
from .models import PlanAnnualAttribute, PlanAttribute
from moderation.models import ModeratedObject
from moderation.constants import (MODERATION_DRAFT_STATE, MODERATION_ADD_STATE, MODERATION_DELETE_STATE,
                                  MODERATION_STATUS_APPROVED, MODERATION_STATUS_PENDING)


class PensionTest(TestCase):
    """
    This results "fails" in moderation mode
    """
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

        # add new obj with calculated attr
        response = self.client.post(url, {'attr_id': self.plan_calculated_attr.id,
                                          'plan_id': self.plan.id,
                                          'year': '2016',
                                          'value': '2'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(response['result'], 'success')
        self.assertEqual(
            PlanAnnualAttribute.objects.get(plan=self.plan, year='2016',
                                            plan_attribute=self.plan_calculated_attr).attribute_value,
            '0'  # '2' if not trigger
        )

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

    def test_trigger_when_edit_calc_rule(self):
        print('-------------Trigger test---------------')
        # print(PlanAnnualAttribute.objects.get(id=self.plan_annual_attr_with_calc_rule.id).attribute_value)
        self.plan_calculated_attr.calculated_rule = '#%123%#'
        self.plan_calculated_attr.save()
        # print(PlanAnnualAttribute.objects.get(id=self.plan_annual_attr_with_calc_rule.id).attribute_value)

        self.assertEqual(PlanAnnualAttribute.objects.get(id=self.plan_annual_attr_with_calc_rule.id).attribute_value,
                         '123')


class PensionModerationTest(TestCase):
    def setUp(self):
        self.create_init_data()

        self.add_url = reverse('pensiondata:add_plan_annual_attr')
        self.edit_url = reverse('pensiondata:edit_plan_annual_attr')
        self.del_url = reverse('pensiondata:delete_plan_annual_attr')
        self.login_admin()

    def test_del_planannualattr(self):
        print('--------------Del test---------------')

        self.assertTrue(PlanAnnualAttribute.objects.filter(id=self.plan_annual_attr.pk).exists())

        response = self.client.post(self.del_url, {'attr_id': self.plan_annual_attr.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(PlanAnnualAttribute.objects.filter(id=self.plan_annual_attr.pk).exists())

        mods = ModeratedObject.objects.all()
        self.assertEqual(len(mods), 2)
        for m in mods:
            self.assertTrue([m.state, m.status] in [[MODERATION_ADD_STATE, MODERATION_STATUS_APPROVED],
                                                    [MODERATION_DELETE_STATE, MODERATION_STATUS_PENDING]])

        # approve
        url = reverse('admin:moderation_moderatedobject_change',
                      args=(self.plan_annual_attr.moderated_object.pk,))

        response = self.client.post(url, {'approve': 'Approve',
                                          'reason': 'this is reason'})

        self.assertEqual(response.status_code, 302)

        # for obj in self.plan_annual_attr.moderated_objects:
        #     obj.approve(by=self.admin)

        self.assertFalse(PlanAnnualAttribute.objects.filter(id=self.plan_annual_attr.pk).exists())

        mods = ModeratedObject.objects.all()
        self.assertEqual(len(mods), 0)

    def test_add_planannualattr(self):
        print('--------------Add test---------------')

        # already exists
        response = self.client.post(self.add_url, {'attr_id': self.plan_static_attr1.id,
                                                   'plan_id': self.plan.id,
                                                   'year': '2017',
                                                   'value': '2'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(response['result'], 'fail')

        # add new obj with calculated attr
        response = self.client.post(self.add_url, {'attr_id': self.plan_calculated_attr.id,
                                                   'plan_id': self.plan.id,
                                                   'year': '2016',
                                                   'value': '2'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(response['result'], 'success')
        self.assertFalse(PlanAnnualAttribute.objects.filter(plan=self.plan, year='2016', plan_attribute=self.plan_calculated_attr).exists())

        mods = ModeratedObject.objects.all()
        self.assertEqual(len(mods), 1)
        for m in mods:
            self.assertTrue([m.state, m.status] in [[MODERATION_ADD_STATE, MODERATION_STATUS_PENDING]])

        # ----- approve
        for m in mods:
            m.approve(by=self.admin)

        new_plan_annual_attr = PlanAnnualAttribute.objects.get(plan=self.plan, year='2016',
                                                               plan_attribute=self.plan_calculated_attr)
        self.assertEqual(new_plan_annual_attr.attribute_value, '0')  # '2' if not trigger

        # # ----- delete: should be created a new moderated obj.
        #
        # response = self.client.post(del_url, {'attr_id': new_plan_annual_attr.pk}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # self.assertTrue(PlanAnnualAttribute.objects.filter(id=new_plan_annual_attr.pk).exists())
        #
        # mods = ModeratedObject.objects.all()
        # self.assertEqual(len(mods), 2)
        # for m in mods:
        #     self.assertTrue([m.state, m.status] in [[MODERATION_ADD_STATE, MODERATION_STATUS_APPROVED],
        #                                             [MODERATION_DELETE_STATE, MODERATION_STATUS_PENDING]])

        # add new obj with static attr
        response = self.client.post(self.add_url, {'attr_id': self.plan_static_attr1.id,
                                                   'plan_id': self.plan.id,
                                                   'year': '2016',
                                                   'value': '2'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        response = json.loads(response.content)
        self.assertEqual(response['result'], 'success')
        # ----- false because signal is not triggered.
        self.assertFalse(PlanAnnualAttribute.objects.filter(plan=self.plan, year='2016', plan_attribute=self.plan_static_attr1).exists())

    def test_edit_planannualattr(self):
        print('--------------Edit test---------------')

        # plan_annual_attr_with_static2 old_val = 222
        response = self.client.post(self.edit_url, {'attr_id': self.plan_annual_attr_with_static2.id, 'new_val': '2'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlanAnnualAttribute.objects.get(id=self.plan_annual_attr_with_static2.id).attribute_value,
                         '222')  # not 2

        mods = ModeratedObject.objects.all()
        self.assertEqual(len(mods), 2)
        for m in mods:
            self.assertTrue([m.state, m.status] in [[MODERATION_ADD_STATE, MODERATION_STATUS_APPROVED],
                                                    [MODERATION_DRAFT_STATE, MODERATION_STATUS_PENDING]])
        # ----- approve
        for m in mods:
            m.approve(by=self.admin)

        self.assertEqual(PlanAnnualAttribute.objects.get(id=self.plan_annual_attr_with_static2.id).attribute_value,
                         '2')  # changed to 2

        # check signal: should not trigger signal
        static_value1 = 111
        static_value2 = 2
        self.assertEqual(PlanAnnualAttribute.objects.get(id=self.plan_annual_attr_with_calc_rule.id).attribute_value,
                         str(static_value1*100-(200/3)+static_value2))

        # ----- delete: should be created a new moderated obj.

        response = self.client.post(self.del_url, {'attr_id': self.plan_annual_attr_with_static2.id},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(PlanAnnualAttribute.objects.filter(id=self.plan_annual_attr_with_static2.id).exists())

        mods = ModeratedObject.objects.all()
        self.assertEqual(len(mods), 3)
        for m in mods:
            self.assertTrue([m.state, m.status] in [[MODERATION_ADD_STATE, MODERATION_STATUS_APPROVED],
                                                    [MODERATION_DRAFT_STATE, MODERATION_STATUS_APPROVED],
                                                    [MODERATION_DELETE_STATE, MODERATION_STATUS_PENDING]])

