from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MyPluginSettingsView,
    EquipmentLoanViewSet,
    LoanListView,
    LoanStatisticsView,
)
from .views import LoanManagementPageView

# Create a router and register the viewsets
router = DefaultRouter()
router.register(r"loans", EquipmentLoanViewSet, basename="equipment-loan")

urlpatterns = [
    # Include routed viewsets
    path("", include(router.urls)),
    # Other endpoints
    path("settings/", MyPluginSettingsView.as_view(), name="equipmentloan-settings"),
    path("loans/list/", LoanListView.as_view(), name="loan-list"),
    path("loans/statistics/", LoanStatisticsView.as_view(), name="loan-statistics"),
    # Frontend page for the loan management UI
    path("page/", LoanManagementPageView.as_view(), name="equipmentloan-page"),
]
