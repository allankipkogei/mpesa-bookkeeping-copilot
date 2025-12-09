from django.urls import path
from transactions.views import TransactionListCreateView
from auth_app.views import UserCreateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("auth/register/", UserCreateView.as_view(), name="register"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("transactions/", TransactionListCreateView.as_view(), name="transactions"),
]
