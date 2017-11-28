from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.dispatch import receiver
from .models import PlanAnnualAttribute, PlanAttribute, GovernmentAnnualAttribute, GovernmentAttribute
from django.db.models import Q


@receiver(post_save, sender=PlanAnnualAttribute)
@receiver(post_delete, sender=PlanAnnualAttribute)
@receiver(post_save, sender=PlanAttribute)
@receiver(post_save, sender=GovernmentAnnualAttribute)
@receiver(post_delete, sender=GovernmentAnnualAttribute)
@receiver(post_save, sender=GovernmentAttribute)
def recalculate(sender, instance, **kwargs):

    post_save.disconnect(recalculate, sender=PlanAnnualAttribute)
    post_save.disconnect(recalculate, sender=PlanAttribute)
    post_save.disconnect(recalculate, sender=GovernmentAnnualAttribute)
    post_save.disconnect(recalculate, sender=GovernmentAttribute)
    # print('Instance: {}'.format(instance.__dict__))

    if sender is PlanAnnualAttribute:
        obj_list = PlanAnnualAttribute.objects.filter(
            plan=instance.plan,
            year=instance.year
        ).filter(
            Q(plan_attribute__attribute_type='calculated') | Q(plan_attribute__data_source__id=0)  # NOTE: hardcoded
        ).select_related('plan_attribute', 'plan_attribute__data_source')

    elif sender is GovernmentAnnualAttribute:
        obj_list = GovernmentAnnualAttribute.objects.filter(
            government=instance.government,
            year=instance.year
        ).filter(
            Q(government_attribute__attribute_type='calculated') | Q(government_attribute__data_source__id=0)  # NOTE: hardcoded
        ).select_related('government_attribute', 'government_attribute__data_source')

    elif sender is PlanAttribute:
        # print('Signal in PlanAttribute')
        if not instance.is_static:  # calculated
            obj_list = PlanAnnualAttribute.objects.filter(plan_attribute=instance)
        else:
            obj_list = PlanAnnualAttribute.objects.filter(plan_attribute=instance, is_from_source=True)

    elif sender is GovernmentAttribute:
        print('Signal in GovernmentAttribute')
        if not instance.is_static:  # calculated
            obj_list = GovernmentAnnualAttribute.objects.filter(government_attribute=instance)
        else:
            obj_list = GovernmentAnnualAttribute.objects.filter(government_attribute=instance, is_from_source=True)

    else:
        obj_list = []

    for obj in obj_list:
        obj.attribute_value = obj.value
        obj.save()

    post_save.connect(recalculate, sender=PlanAnnualAttribute)
    post_save.connect(recalculate, sender=PlanAttribute)
    post_save.connect(recalculate, sender=GovernmentAnnualAttribute)
    post_save.connect(recalculate, sender=GovernmentAttribute)




