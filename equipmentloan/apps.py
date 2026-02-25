"""
App configuration for the EquipmentLoan plugin.
"""

from django.apps import AppConfig


class EquipmentLoanConfig(AppConfig):
    """
    AppConfig for the EquipmentLoan plugin.
    """

    name = "equipmentloan"
    verbose_name = "Equipment Loan"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """Initialize the app when Django is ready."""
        # Import signals or perform other initialization here if needed
        pass
