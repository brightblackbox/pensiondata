from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.dispatch import receiver
from .models import PlanAnnualAttribute, PlanAttribute
from django.db.models import Q


@receiver(post_save, sender=PlanAnnualAttribute)
@receiver(post_delete, sender=PlanAnnualAttribute)
@receiver(post_save, sender=PlanAttribute)
def recalculate(sender, instance, **kwargs):

    post_save.disconnect(recalculate, sender=PlanAnnualAttribute)
    post_save.disconnect(recalculate, sender=PlanAttribute)
    # print('Instance: {}'.format(instance.__dict__))

    if sender is PlanAnnualAttribute:
        obj_list = PlanAnnualAttribute.objects.filter(
            plan=instance.plan,
            year=instance.year
        ).filter(
            Q(plan_attribute__attribute_type='calculated') | Q(plan_attribute__data_source__id=0)  # NOTE: hardcoded
        ).select_related('plan_attribute', 'plan_attribute__data_source')

        for obj in obj_list:
            obj.attribute_value = obj.value
            obj.save()

    elif sender is PlanAttribute:
        # print('Signal in PlanAttribute')
        if not instance.is_static:  # calculated
            obj_list = PlanAnnualAttribute.objects.filter(plan_attribute=instance)
        else:
            obj_list = PlanAnnualAttribute.objects.filter(plan_attribute=instance, is_from_source=True)

        for obj in obj_list:
            obj.attribute_value = obj.value
            obj.save()
    else:
        pass

    post_save.connect(recalculate, sender=PlanAnnualAttribute)
    post_save.connect(recalculate, sender=PlanAttribute)




