"""
Models for the EquipmentLoan plugin.
Tracks the borrowing and return of equipment/parts.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.utils import timezone


class EquipmentLoan(models.Model):
    """
    Track equipment/parts that are being borrowed by users.

    This model maintains a record of:
    - Who is borrowing the equipment
    - What part/equipment they borrowed
    - When it was borrowed
    - When it was returned (if applicable)
    - Any notes or conditions of the loan
    """

    # Status choices for the loan
    LOAN_STATUS_CHOICES = [
        ("active", _("Active - Currently Borrowed")),
        ("returned", _("Returned")),
        ("overdue", _("Overdue")),
        ("lost", _("Lost")),
    ]

    # Primary fields
    borrower = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="equipment_loans",
        help_text=_("User who borrowed the equipment"),
    )

    part_id = models.IntegerField(
        null=False, blank=False, help_text=_("InvenTree Part ID being borrowed")
    )

    part_name = models.CharField(
        max_length=255,
        help_text=_("Name of the part being borrowed (cached for reference)"),
    )

    quantity = models.IntegerField(default=1, help_text=_("Quantity of parts borrowed"))

    # Loan duration fields
    date_borrowed = models.DateTimeField(
        auto_now_add=True, help_text=_("When the equipment was borrowed")
    )

    date_due = models.DateTimeField(
        null=True, blank=True, help_text=_("Expected return date")
    )

    date_returned = models.DateTimeField(
        null=True, blank=True, help_text=_("When the equipment was actually returned")
    )

    # Status and notes
    status = models.CharField(
        max_length=20,
        choices=LOAN_STATUS_CHOICES,
        default="active",
        help_text=_("Current status of the loan"),
    )

    notes = models.TextField(blank=True, help_text=_("Additional notes about the loan"))

    return_notes = models.TextField(
        blank=True, help_text=_("Condition notes when returned")
    )

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="loans_created",
        help_text=_("User who recorded the loan"),
    )

    date_created = models.DateTimeField(auto_now_add=True)

    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_borrowed"]
        verbose_name = _("Equipment Loan")
        verbose_name_plural = _("Equipment Loans")
        app_label = "equipmentloan"
        indexes = [
            models.Index(fields=["borrower", "status"]),
            models.Index(fields=["part_id", "status"]),
            models.Index(fields=["date_borrowed"]),
        ]

    def __str__(self):
        return f"{self.part_name} borrowed by {self.borrower.username} on {self.date_borrowed.strftime('%Y-%m-%d')}"

    def is_overdue(self):
        """Check if the loan is overdue"""
        if self.date_returned or self.status == "returned":
            return False
        if self.date_due and timezone.now() > self.date_due:
            return True
        return False

    def mark_returned(self, return_notes=""):
        """Mark the equipment as returned"""
        self.date_returned = timezone.now()
        self.status = "returned"
        self.return_notes = return_notes
        self.save()

    def mark_lost(self):
        """Mark the equipment as lost"""
        self.status = "lost"
        self.save()

    def get_days_borrowed(self):
        """Calculate number of days equipment has been borrowed"""
        end_date = self.date_returned or timezone.now()
        delta = end_date - self.date_borrowed
        return delta.days

    def get_days_overdue(self):
        """Calculate number of days overdue (if applicable)"""
        if not self.is_overdue():
            return 0
        delta = timezone.now() - self.date_due
        return delta.days


class LoanHistory(models.Model):
    """
    Audit trail for equipment loan events.
    Tracks all changes and actions related to loans.
    """

    EVENT_TYPES = [
        ("created", _("Loan Created")),
        ("returned", _("Equipment Returned")),
        ("extended", _("Due Date Extended")),
        ("marked_lost", _("Marked as Lost")),
        ("status_changed", _("Status Changed")),
        ("notes_updated", _("Notes Updated")),
    ]

    loan = models.ForeignKey(
        EquipmentLoan, on_delete=models.CASCADE, related_name="history"
    )

    event_type = models.CharField(
        max_length=20, choices=EVENT_TYPES, help_text=_("Type of event")
    )

    description = models.TextField(help_text=_("Description of what happened"))

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("User who triggered this event"),
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Loan History")
        verbose_name_plural = _("Loan Histories")
        app_label = "equipmentloan"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["loan", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.loan} at {self.timestamp}"
