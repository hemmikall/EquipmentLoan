"""
Serializers for EquipmentLoan plugin models.
"""

from rest_framework import serializers
from .models import EquipmentLoan, LoanHistory


class LoanHistorySerializer(serializers.ModelSerializer):
    """Serializer for LoanHistory model"""

    user_username = serializers.CharField(source="user.username", read_only=True)
    event_type_display = serializers.CharField(
        source="get_event_type_display", read_only=True
    )

    class Meta:
        model = LoanHistory
        fields = [
            "id",
            "event_type",
            "event_type_display",
            "description",
            "user",
            "user_username",
            "timestamp",
        ]
        read_only_fields = ["id", "user", "timestamp"]


class EquipmentLoanSerializer(serializers.ModelSerializer):
    """Serializer for EquipmentLoan model"""

    borrower_username = serializers.CharField(
        source="borrower.username", read_only=True
    )
    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True, allow_null=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_overdue = serializers.SerializerMethodField()
    days_borrowed = serializers.SerializerMethodField()
    days_overdue = serializers.SerializerMethodField()
    history = LoanHistorySerializer(many=True, read_only=True)

    class Meta:
        model = EquipmentLoan
        fields = [
            "id",
            "borrower",
            "borrower_username",
            "part_id",
            "part_name",
            "quantity",
            "date_borrowed",
            "date_due",
            "date_returned",
            "status",
            "status_display",
            "notes",
            "return_notes",
            "created_by",
            "created_by_username",
            "date_created",
            "date_updated",
            "is_overdue",
            "days_borrowed",
            "days_overdue",
            "history",
        ]
        read_only_fields = [
            "date_borrowed",
            "date_created",
            "date_updated",
            "created_by",
        ]

    def get_is_overdue(self, obj):
        """Check if loan is overdue"""
        return obj.is_overdue()

    def get_days_borrowed(self, obj):
        """Get number of days borrowed"""
        return obj.get_days_borrowed()

    def get_days_overdue(self, obj):
        """Get number of days overdue"""
        return obj.get_days_overdue()


class EquipmentLoanListSerializer(serializers.ModelSerializer):
    """Simplified serializer for loan list views"""

    borrower_username = serializers.CharField(
        source="borrower.username", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_overdue = serializers.SerializerMethodField()
    days_borrowed = serializers.SerializerMethodField()

    class Meta:
        model = EquipmentLoan
        fields = [
            "id",
            "borrower_username",
            "part_name",
            "quantity",
            "date_borrowed",
            "date_due",
            "date_returned",
            "status",
            "status_display",
            "is_overdue",
            "days_borrowed",
        ]
        read_only_fields = fields

    def get_is_overdue(self, obj):
        return obj.is_overdue()

    def get_days_borrowed(self, obj):
        return obj.get_days_borrowed()
