"""Adds functionality to loan out equipment"""

from equipmentloan import urls
from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, UserInterfaceMixin, UrlsMixin

from . import PLUGIN_VERSION


class EquipmentLoan(SettingsMixin, UserInterfaceMixin, UrlsMixin, InvenTreePlugin):
    """EquipmentLoan - custom InvenTree plugin."""

    # Plugin metadata
    TITLE = "EquipmentLoan"
    NAME = "EquipmentLoan"
    SLUG = "equipmentloan"
    DESCRIPTION = "Adds functionality to loan out equipment"
    VERSION = PLUGIN_VERSION

    # Additional project information
    AUTHOR = "Hermann K Bjornsson"
    WEBSITE = "https://my-project-url.com"
    LICENSE = "GPL-2.0"

    # Optionally specify supported InvenTree versions
    # MIN_VERSION = '0.18.0'
    # MAX_VERSION = '2.0.0'

    # Render custom UI elements to the plugin settings page
    ADMIN_SOURCE = "Settings.js:renderPluginSettings"

    # Plugin settings (from SettingsMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/settings/
    SETTINGS = {
        # Define your plugin settings here...
        "CUSTOM_VALUE": {
            "name": "Custom Value",
            "description": "A custom value",
            "validator": int,
            "default": 42,
        },
        "EQUIPMENTLOAN_LOAN_EQUIPMENT": {
            "name": "Allow Equipment Loan",
            "description": "Allow equipment to be loaned out to users",
            "validator": bool,
            "default": True,
        },
        "EQUIPMENTLOAN_ALLOWED_GROUPS": {
            "name": "Allowed Groups",
            "description": "Comma-separated list of user group names allowed to register equipment loans. Leave empty to allow all authenticated users.",
            "validator": str,
            "default": "",
        },
        "EQUIPMENTLOAN_REQUIRE_ADMIN_APPROVAL": {
            "name": "Require Admin Approval",
            "description": "Require administrator approval before equipment loans are registered",
            "validator": bool,
            "default": False,
        },
    }

    # User interface elements (from UserInterfaceMixin)
    # Ref: https://docs.inventree.org/en/latest/plugins/mixins/ui/

    # Custom UI panels
    def get_ui_panels(self, request, context: dict, **kwargs):
        """Return a list of custom panels to be rendered in the InvenTree user interface."""

        panels = []

        # Only display this panel for the 'part' target
        if context.get("target_model") == "part":
            panels.append({
                "key": "equipmentloan-panel",
                "title": "EquipmentLoan",
                "description": "Custom panel description",
                "icon": "ti:mood-smile:outline",
                "source": self.plugin_static_file("Panel.js:renderEquipmentLoanPanel"),
                "context": {
                    # Provide additional context data to the panel
                    "settings": self.get_settings_dict(),
                    "foo": "bar",
                },
            })
            panels.append({
                "key": "equipmentloan-panel2",
                "title": "EquipmentLoan 2",
                "description": "Custom panel description",
                "icon": "ti:mood-smile:outline",
                "source": self.plugin_static_file(
                    "Panel2.js:renderEquipmentLoanPanel2"
                ),
                "context": {
                    # Provide additional context data to the panel
                    "settings": self.get_settings_dict(),
                    "foo": "bar",
                },
            })

        return panels

    # Custom dashboard items
    def get_ui_dashboard_items(self, request, context: dict, **kwargs):
        """Return a list of custom dashboard items to be rendered in the InvenTree user interface."""

        items = []

        # Equipment Loan Management - accessible to all users
        items.append({
            "key": "equipmentloan-management",
            "title": "Equipment Loans",
            "description": "Manage equipment loans and track borrowing",
            "icon": "ti:package:outline",
            "source": self.plugin_static_file(
                "LoanManagement.js:renderEquipmentLoanManagement"
            ),
            "context": {
                "settings": self.get_settings_dict(),
            },
        })

        return items

    # Custom navigation items (top navigation)
    def get_ui_navigation_items(self, request, context, **kwargs):
        """Return a list of custom navigation items for the top navigation.

        Uses the UserInterfaceMixin contract (as in SampleUI) to register a
        navigation entry which will render the plugin component.
        """
        return [
            {
                "key": "equipmentloan-management",
                "title": "Equipment Loans",
                "icon": "ti:package:outline",
                # Use a URL option so the top-navigation will open our plugin page
                "options": {
                    "url": "/plugins/equipmentloan/page/",
                },
            }
        ]

    def setup_urls(self):
        return urls.urlpatterns
