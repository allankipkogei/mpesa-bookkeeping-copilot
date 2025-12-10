# transactions/views_webhook.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.contrib.auth import get_user_model

from .utils import parse_mpesa_sms
from .models import Transaction

User = get_user_model()

class SmsWebhookView(APIView):
    permission_classes = []  # public for testing; add auth/IP restrictions in production

    def post(self, request):
        """
        Expects JSON like:
        {
            "text": "<MPESA SMS body>",
            "username": "<your-username>"  # optional if phone is provided
            "phone": "<phone number>"       # optional if username is provided
        }
        """
        # Get SMS text
        text = request.data.get("text") or request.data.get("message")
        if not text:
            return Response({"detail": "SMS text required"}, status=status.HTTP_400_BAD_REQUEST)

        # Parse MPESA SMS
        parsed = parse_mpesa_sms(text)
        if not parsed:
            return Response({"detail": "Could not parse SMS"}, status=status.HTTP_400_BAD_REQUEST)

        # Identify user
        username = request.data.get("username")
        phone = request.data.get("phone")
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        elif phone:
            try:
                user = User.objects.get(phone_number=phone)
            except User.DoesNotExist:
                return Response({"detail": "User not found by phone"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"detail": "username or phone required"}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent duplicate transactions
        mpesa_code = parsed.get("mpesa_code")
        if not mpesa_code:
            return Response({"detail": "MPESA code missing from SMS"}, status=status.HTTP_400_BAD_REQUEST)

        if Transaction.objects.filter(user=user, mpesa_code=mpesa_code).exists():
            return Response({"detail": "Transaction already exists"}, status=status.HTTP_200_OK)

        # Create transaction safely
        tx = Transaction.objects.create(
            user=user,
            trans_type=parsed.get("trans_type", "C2B"),
            amount=parsed.get("amount", 0),
            mpesa_code=mpesa_code,
            phone_number=parsed.get("phone_number", ""),
            date=parsed.get("date") or timezone.now(),  # fallback if date missing
        )

        return Response(
            {
                "detail": "Transaction saved",
                "id": tx.id,
                "amount": tx.amount,
                "mpesa_code": tx.mpesa_code,
                "date": tx.date,
            },
            status=status.HTTP_201_CREATED
        )
