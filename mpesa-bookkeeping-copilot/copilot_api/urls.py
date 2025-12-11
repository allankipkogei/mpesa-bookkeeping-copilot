from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from auth_app.views import UserCreateView, CustomTokenObtainPairView
from transactions.views import (
    TransactionListCreateView,
    TransactionDetailView,
    UploadStatementView,
    TransactionSummaryView,
)
from transactions.views_webhook import SmsWebhookView

urlpatterns = [
    # Auth
    path("auth/register/", UserCreateView.as_view(), name="register"),
    path("auth/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Transactions
    path("", TransactionListCreateView.as_view(), name="transaction-list-create"),
    path("<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path("summary/", TransactionSummaryView.as_view(), name="transaction-summary"),
    path("upload-statement/", UploadStatementView.as_view(), name="upload-statement"),

    # Upload statement (CSV / txt) - multipart form
    path("transactions/upload-statement/", UploadStatementView.as_view(), name="upload-statement"),

    # SMS webhook (for SMS ingestion)
    path("webhook/sms/", SmsWebhookView.as_view(), name="sms-webhook"),
]
