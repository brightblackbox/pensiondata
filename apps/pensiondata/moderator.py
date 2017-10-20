from moderation import moderation
from moderation.moderator import GenericModerator

from .models import Plan, PlanAnnualAttribute


class PlanModerator(GenericModerator):
    auto_approve_for_staff = False
    auto_approve_for_superusers = False
    keep_history = True


moderation.register(Plan, PlanModerator)
moderation.register(PlanAnnualAttribute, PlanModerator)
