"""
Permission utilities for the EquipmentLoan plugin.
Handles authorization checks for registering and managing equipment loans.
"""

from rest_framework.permissions import BasePermission


def get_allowed_groups_for_loans(plugin):
    """
    Get the list of allowed groups that can register equipment loans.

    Args:
        plugin: The EquipmentLoan plugin instance

    Returns:
        list: Group names allowed to register loans, or None if all users allowed
    """
    allowed_groups_setting = plugin.get_setting("EQUIPMENTLOAN_ALLOWED_GROUPS", "")

    if not allowed_groups_setting:
        return None  # No restrictions - all authenticated users allowed

    # Parse comma-separated group names
    group_names = [
        name.strip() for name in allowed_groups_setting.split(",") if name.strip()
    ]
    return group_names if group_names else None


def user_can_register_loan(user, plugin):
    """
    Check if a user is allowed to register an equipment loan.

    Args:
        user: The Django user object
        plugin: The EquipmentLoan plugin instance

    Returns:
        bool: True if user can register loans, False otherwise
    """
    # Must be authenticated
    if not user or not user.is_authenticated:
        return False

    # Check if plugin is enabled
    if not plugin.get_setting("EQUIPMENTLOAN_LOAN_EQUIPMENT"):
        return False

    # Superusers and staff always allowed (unless restricted by groups)
    if user.is_superuser or user.is_staff:
        return True

    # Get allowed groups
    allowed_groups = get_allowed_groups_for_loans(plugin)

    # If no groups specified, all authenticated users allowed
    if allowed_groups is None:
        return True

    # Check if user is in any of the allowed groups
    user_groups = user.groups.values_list("name", flat=True)
    return any(group in allowed_groups for group in user_groups)


def user_can_approve_loan(user, plugin):
    """
    Check if a user is allowed to approve equipment loans.
    (Only staff/admin users can approve)

    Args:
        user: The Django user object
        plugin: The EquipmentLoan plugin instance

    Returns:
        bool: True if user can approve loans, False otherwise
    """
    if not user or not user.is_authenticated:
        return False

    return user.is_staff or user.is_superuser


def user_can_manage_loan(user, loan, plugin):
    """
    Check if a user can manage a specific loan (view, return, modify).

    Args:
        user: The Django user object
        loan: The EquipmentLoan instance
        plugin: The EquipmentLoan plugin instance

    Returns:
        bool: True if user can manage this loan, False otherwise
    """
    if not user or not user.is_authenticated:
        return False

    # Superusers and staff can manage any loan
    if user.is_superuser or user.is_staff:
        return True

    # Borrowers can manage their own loans
    return loan.borrower == user


class CanRegisterLoanPermission(BasePermission):
    """
    Custom DRF permission for registering equipment loans.
    Checks if user is in allowed groups.
    """

    def has_permission(self, request, view):
        """Check if user can register a loan"""
        plugin = request.inventree_plugins.get("equipmentloan")
        if not plugin:
            return False
        return user_can_register_loan(request.user, plugin)


class CanApproveLoanPermission(BasePermission):
    """
    Custom DRF permission for approving equipment loans.
    Only staff/admin users allowed.
    """

    def has_permission(self, request, view):
        """Check if user can approve loans"""
        plugin = request.inventree_plugins.get("equipmentloan")
        if not plugin:
            return False
        return user_can_approve_loan(request.user, plugin)


class CanManageLoanPermission(BasePermission):
    """
    Custom DRF permission for managing a specific loan.
    Borrowers can manage their own, staff can manage all.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user can manage this specific loan"""
        plugin = request.inventree_plugins.get("equipmentloan")
        if not plugin:
            return False
        return user_can_manage_loan(request.user, obj, plugin)
