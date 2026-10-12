"""Role-based API access control for Didebaan operational users."""
from rest_framework.permissions import BasePermission, SAFE_METHODS

ROLE_AUDITOR = 'AUDITOR'
ROLE_INVESTIGATOR = 'INVESTIGATOR'
ROLE_SUPERVISOR = 'SUPERVISOR'
ROLE_COMPLIANCE = 'COMPLIANCE_OFFICER'
ROLE_NAMES = (ROLE_AUDITOR, ROLE_INVESTIGATOR, ROLE_SUPERVISOR, ROLE_COMPLIANCE)

READ_ROLES = set(ROLE_NAMES)
CASEWORK_ROLES = {ROLE_INVESTIGATOR, ROLE_SUPERVISOR, ROLE_COMPLIANCE}
MANAGEMENT_ROLES = {ROLE_SUPERVISOR, ROLE_COMPLIANCE}
COMPLIANCE_ROLES = {ROLE_COMPLIANCE}


def user_roles(user):
    if not user or not user.is_authenticated:
        return set()
    if user.is_superuser:
        return set(ROLE_NAMES)
    return set(user.groups.filter(name__in=ROLE_NAMES).values_list('name', flat=True))


class RolePermission(BasePermission):
    """Base permission for API views backed by Didebaan role groups."""

    roles = READ_ROLES

    def has_permission(self, request, view):
        return bool(user_roles(request.user) & self.roles)


class ReadOnlyRolePermission(RolePermission):
    """All operational roles can read; compliance officers can change records."""

    def has_permission(self, request, view):
        roles = user_roles(request.user)
        return bool(roles & (READ_ROLES if request.method in SAFE_METHODS else COMPLIANCE_ROLES))


class CompliancePermission(RolePermission):
    roles = COMPLIANCE_ROLES


class AlertPermission(RolePermission):
    """Limit case actions to their appropriate operational role."""

    def has_permission(self, request, view):
        roles = user_roles(request.user)
        action = getattr(view, 'action', None)

        if request.method in SAFE_METHODS or action in {'statistics', 'open_count', 'export', 'comments_export'}:
            return bool(roles & READ_ROLES)
        if action in {'assign_alert', 'bulk_assign', 'bulk_review'}:
            return bool(roles & MANAGEMENT_ROLES)
        if action in {'review_alert', 'comments'}:
            return bool(roles & CASEWORK_ROLES)
        return bool(roles & MANAGEMENT_ROLES)

    def has_object_permission(self, request, view, obj):
        roles = user_roles(request.user)
        action = getattr(view, 'action', None)
        if action not in {'review_alert', 'comments'} or request.method in SAFE_METHODS:
            return True
        if roles & MANAGEMENT_ROLES:
            return True
        return obj.assigned_to == request.user.get_username()
