from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from auth_app.views import UserCreateView
from transactions.views import (
    TransactionListCreateView,
    TransactionDetailView,
    UploadStatementView,
)
from transactions.views_webhook import SmsWebhookView

urlpatterns = [
    # Auth
    path("auth/register/", UserCreateView.as_view(), name="register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Transactions
    path("transactions/", TransactionListCreateView.as_view(), name="transactions"),
    path("transactions/<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),

    # Upload statement (CSV / txt) - multipart form
    path("transactions/upload-statement/", UploadStatementView.as_view(), name="upload-statement"),

    # SMS webhook (for SMS ingestion)
    path("webhook/sms/", SmsWebhookView.as_view(), name="sms-webhook"),
]
