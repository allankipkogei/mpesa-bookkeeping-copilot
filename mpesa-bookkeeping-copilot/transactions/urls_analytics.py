from django.urls import path
from .views_analytics import (
    MonthlyAnalyticsView,
    TopCategoriesView,
    CashflowView,
    RecurringPaymentsView,
    SpendingTrendsView,
    BudgetInsightsView
)

urlpatterns = [
    path("monthly/", MonthlyAnalyticsView.as_view(), name="monthly-analytics"),
    path("top-categories/", TopCategoriesView.as_view(), name="top-categories"),
    path("cashflow/", CashflowView.as_view(), name="cashflow-analytics"),
    path("recurring-payments/", RecurringPaymentsView.as_view(), name="recurring-payments"),
    path("spending-trends/", SpendingTrendsView.as_view(), name="spending-trends"),
    path("budget-insights/", BudgetInsightsView.as_view(), name="budget-insights"),
]
