from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .utils import parse_mpesa_sms
from .models import Transaction
from django.utils import timezone

class SmsWebhookView(APIView):
    permission_classes = [permissions.AllowAny]  # depending on gateway security

    def post(self, request):
        text = request.data.get("text") or request.data.get("message") or ""
        parsed = parse_mpesa_sms(text)
        if not parsed:
            return Response({"detail":"Could not parse SMS"}, status=status.HTTP_400_BAD_REQUEST)
        # For MVP, associate to a default user or find by phone number
        # Here we require the webhook to include 'username' to map incoming SMS
        username = request.data.get("username")
        if not username:
            return Response({"detail":"username required"}, status=status.HTTP_400_BAD_REQUEST)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"detail":"user not found"}, status=status.HTTP_404_NOT_FOUND)

        tx = Transaction.objects.create(
            user=user,
            trans_type="C2B",
            amount=parsed["amount"],
            mpesa_code=parsed["mpesa_code"],
            date=timezone.now()
        )
        return Response({"id": tx.id}, status=status.HTTP_201_CREATED)
