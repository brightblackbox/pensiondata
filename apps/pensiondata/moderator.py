from moderation import moderation
from moderation.moderator import GenericModerator

from .models import Plan, PlanAnnualAttribute, Government, GovernmentAnnualAttribute


class PlanModerator(GenericModerator):
    auto_approve_for_staff = False
    auto_approve_for_superusers = False
    keep_history = True


moderation.register(Plan, PlanModerator)
moderation.register(PlanAnnualAttribute, PlanModerator)


class GovernmentModerator(GenericModerator):
    auto_approve_for_staff = False
    auto_approve_for_superusers = False
    keep_history = True


moderation.register(Government, GovernmentModerator)
moderation.register(GovernmentAnnualAttribute, GovernmentModerator)
