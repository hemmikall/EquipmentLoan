"""Adds functionality to loan out equipment"""

from plugin import InvenTreePlugin

from plugin.mixins import SettingsMixin, UserInterfaceMixin

from . import PLUGIN_VERSION


class EquipmentLoan(SettingsMixin, UserInterfaceMixin, InvenTreePlugin):
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
        }
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

        return panels

    # Custom dashboard items
    def get_ui_dashboard_items(self, request, context: dict, **kwargs):
        """Return a list of custom dashboard items to be rendered in the InvenTree user interface."""

        # Example: only display for 'staff' users
        if not request.user or not request.user.is_staff:
            return []

        items = []

        items.append({
            "key": "equipmentloan-dashboard",
            "title": "EquipmentLoan Dashboard Item",
            "description": "Custom dashboard item",
            "icon": "ti:dashboard:outline",
            "source": self.plugin_static_file(
                "Dashboard.js:renderEquipmentLoanDashboardItem"
            ),
            "context": {
                # Provide additional context data to the dashboard item
                "settings": self.get_settings_dict(),
                "bar": "foo",
            },
        })

        return items
