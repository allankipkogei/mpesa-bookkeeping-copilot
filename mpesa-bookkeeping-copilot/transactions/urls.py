from django.urls import path
from .views import (
    TransactionListCreateView, 
    TransactionDetailView, 
    TransactionSummaryView,
    UploadStatementView,
    CategorizeTransactionView,
    BulkCategorizeView,
    CategorySuggestionsView,
    CategoryListView,
    CategoryStatsView,
    UpdateTransactionCategoryView
)

urlpatterns = [
    path("", TransactionListCreateView.as_view(), name="transaction-list-create"),
    path("<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path("summary/", TransactionSummaryView.as_view(), name="transaction-summary"),
    path("upload/", UploadStatementView.as_view(), name="upload-statement"),
    
    # Categorization endpoints
    path("<int:pk>/categorize/", CategorizeTransactionView.as_view(), name="categorize-transaction"),
    path("<int:pk>/category/", UpdateTransactionCategoryView.as_view(), name="update-category"),
    path("bulk-categorize/", BulkCategorizeView.as_view(), name="bulk-categorize"),
    path("category-suggestions/", CategorySuggestionsView.as_view(), name="category-suggestions"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("category-stats/", CategoryStatsView.as_view(), name="category-stats"),
]
