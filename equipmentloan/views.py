from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.utils import timezone
from .models import EquipmentLoan, LoanHistory
from .serializers import (
    EquipmentLoanSerializer,
    EquipmentLoanListSerializer,
)
from .permissions import (
    user_can_register_loan,
)
from django.views.generic import TemplateView


class MyPluginSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plugin = request.inventree_plugins.get("equipmentloan")

        return Response({
            "CUSTOM_VALUE": plugin.get_setting("CUSTOM_VALUE"),
            "EQUIPMENTLOAN_LOAN_EQUIPMENT": plugin.get_setting(
                "EQUIPMENTLOAN_LOAN_EQUIPMENT"
            ),
            "EQUIPMENTLOAN_ALLOWED_GROUPS": plugin.get_setting(
                "EQUIPMENTLOAN_ALLOWED_GROUPS"
            ),
            "EQUIPMENTLOAN_REQUIRE_ADMIN_APPROVAL": plugin.get_setting(
                "EQUIPMENTLOAN_REQUIRE_ADMIN_APPROVAL"
            ),
        })


class EquipmentLoanViewSet(viewsets.ModelViewSet):
    """
    API viewset for managing equipment loans.
    """

    queryset = EquipmentLoan.objects.all()
    serializer_class = EquipmentLoanSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Use simplified serializer for list view"""
        if self.action == "list":
            return EquipmentLoanListSerializer
        return EquipmentLoanSerializer

    def get_queryset(self):
        """Filter loans based on user permissions"""
        queryset = EquipmentLoan.objects.all()

        # Staff can see all loans
        if self.request.user.is_staff:
            return queryset

        # Regular users only see their own loans
        return queryset.filter(borrower=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create a new equipment loan"""
        plugin = request.inventree_plugins.get("equipmentloan")

        # Check if user can register loans
        if not user_can_register_loan(request.user, plugin):
            return Response(
                {"error": "You do not have permission to register equipment loans."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate required fields
        if "part_id" not in request.data or "part_name" not in request.data:
            return Response(
                {"error": "part_id and part_name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set the borrower to current user if not specified
        request.data["borrower"] = request.user.id
        request.data["created_by"] = request.user.id

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Create history entry
        loan = serializer.instance
        LoanHistory.objects.create(
            loan=loan,
            event_type="created",
            description=f"Equipment loan created: {loan.part_name} (qty: {loan.quantity})",
            user=request.user,
        )

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_update(self, serializer):
        """Update a loan"""
        serializer.save()

    @action(detail=True, methods=["post"])
    def mark_returned(self, request, pk=None):
        """Mark equipment as returned"""
        loan = self.get_object()

        # Check permissions
        if not request.user.is_staff and loan.borrower != request.user:
            return Response(
                {"error": "You do not have permission to manage this loan."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return_notes = request.data.get("return_notes", "")
        loan.mark_returned(return_notes=return_notes)

        # Create history entry
        LoanHistory.objects.create(
            loan=loan,
            event_type="returned",
            description=f"Equipment returned: {loan.part_name}",
            user=request.user,
        )

        serializer = self.get_serializer(loan)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def mark_lost(self, request, pk=None):
        """Mark equipment as lost"""
        loan = self.get_object()

        # Check permissions
        if not request.user.is_staff:
            return Response(
                {"error": "Only staff can mark equipment as lost."},
                status=status.HTTP_403_FORBIDDEN,
            )

        loan.mark_lost()

        # Create history entry
        LoanHistory.objects.create(
            loan=loan,
            event_type="marked_lost",
            description=f"Equipment marked as lost: {loan.part_name}",
            user=request.user,
        )

        serializer = self.get_serializer(loan)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def extend_due_date(self, request, pk=None):
        """Extend the due date of a loan"""
        loan = self.get_object()

        # Check permissions
        if not request.user.is_staff and loan.borrower != request.user:
            return Response(
                {"error": "You do not have permission to manage this loan."},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_due_date = request.data.get("date_due")
        if not new_due_date:
            return Response(
                {"error": "date_due is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        old_due_date = loan.date_due
        loan.date_due = new_due_date
        loan.save()

        # Create history entry
        LoanHistory.objects.create(
            loan=loan,
            event_type="extended",
            description=f"Due date extended from {old_due_date} to {new_due_date}",
            user=request.user,
        )

        serializer = self.get_serializer(loan)
        return Response(serializer.data)


class LoanListView(APIView):
    """
    API endpoint for listing all equipment loans with filtering.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get filtered list of loans"""
        queryset = EquipmentLoan.objects.all()

        # Staff can see all loans
        if not request.user.is_staff:
            queryset = queryset.filter(borrower=request.user)

        # Filter by status
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by borrower (staff only)
        if request.user.is_staff:
            borrower_id = request.query_params.get("borrower_id")
            if borrower_id:
                queryset = queryset.filter(borrower_id=borrower_id)

        # Filter by part
        part_id = request.query_params.get("part_id")
        if part_id:
            queryset = queryset.filter(part_id=part_id)

        # Filter overdue loans
        show_overdue = request.query_params.get("overdue_only")
        if show_overdue == "true":
            queryset = queryset.filter(status="active", date_due__lt=timezone.now())

        # Order by date
        queryset = queryset.order_by("-date_borrowed")

        serializer = EquipmentLoanListSerializer(queryset, many=True)
        return Response({"count": queryset.count(), "results": serializer.data})


class LoanStatisticsView(APIView):
    """
    API endpoint for loan statistics.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get loan statistics"""
        queryset = EquipmentLoan.objects.all()

        # Regular users only see their own statistics
        if not request.user.is_staff:
            queryset = queryset.filter(borrower=request.user)

        stats = {
            "total_loans": queryset.count(),
            "active_loans": queryset.filter(status="active").count(),
            "returned_loans": queryset.filter(status="returned").count(),
            "lost_loans": queryset.filter(status="lost").count(),
            "overdue_loans": queryset.filter(
                status="active", date_due__isnull=False, date_due__lt=timezone.now()
            ).count(),
        }

        return Response(stats)


class LoanManagementPageView(TemplateView):
    """Render a simple page that mounts the compiled frontend bundle for loan management."""

    template_name = "equipmentloan/management.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Add any server-side context here if needed
        return ctx
