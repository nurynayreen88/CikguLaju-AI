"""Staging-only read-only teacher confirmation handoff."""
from .taught_confirmation_guard import Confirmation, validate_confirmation


def check_taught_action(confirmation, explicit_action=False):
    if explicit_action is not True:
        return False, "teacher_confirmation_required"
    if not isinstance(confirmation, Confirmation):
        return False, "invalid_confirmation"
    decision = validate_confirmation(confirmation)
    return decision.allowed, decision.reason
