from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.dispatch import receiver
from .models import PlanAnnualAttribute, PlanAttribute


@receiver(post_save, sender=PlanAnnualAttribute)
@receiver(post_delete, sender=PlanAnnualAttribute)
@receiver(post_save, sender=PlanAttribute)
def recalculate(sender, instance, **kwargs):
    post_save.disconnect(recalculate, sender=PlanAnnualAttribute)
    post_save.disconnect(recalculate, sender=PlanAttribute)
    # print('Instance: {}'.format(instance.__dict__))

    if sender is PlanAnnualAttribute:
        # print('Signal in PlanAnnualAttribute')
        obj_list = PlanAnnualAttribute.objects.filter(
            plan=instance.plan,
            year=instance.year,
            plan_attribute__attribute_type='calculated'
        ).select_related('plan_attribute')

        for obj in obj_list:
            obj.attribute_value = obj.value
            obj.save()

    elif sender is PlanAttribute:
        # print('Signal in PlanAttribute')
        if not instance.is_static:
            print('here')
            obj_list = PlanAnnualAttribute.objects.filter(plan_attribute=instance)

            for obj in obj_list:
                obj.attribute_value = obj.value
                obj.save()
    else:
        pass

    post_save.connect(recalculate, sender=PlanAnnualAttribute)
    post_save.connect(recalculate, sender=PlanAttribute)




