from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Transaction
import re
from datetime import datetime


class SmsWebhookView(APIView):
    permission_classes = []  # keep open for now, but protected by API key

    def post(self, request):
        # ------------------------------------
        # 1. API KEY SECURITY CHECK
        # ------------------------------------
        api_key = request.headers.get("X-API-KEY")
        if api_key != settings.WEBHOOK_SECRET:
            return Response({"detail": "Invalid or missing API key"}, status=status.HTTP_401_UNAUTHORIZED)

        text = request.data.get("text")
        username = request.data.get("username")

        if not text:
            return Response({"detail": "Missing `text` field"}, status=status.HTTP_400_BAD_REQUEST)

        # ------------------------------------
        # 2. Parse SMS using REGEX
        # ------------------------------------
        try:
            pattern = r"([A-Z0-9]{10}) Confirmed\. You have received Ksh ([\d,]+\.\d{2}) from (\d{12}) on (.+?) at (.+?)\. New M-PESA"
            match = re.search(pattern, text)

            if not match:
                return Response({"detail": "Unrecognized SMS format"}, status=status.HTTP_400_BAD_REQUEST)

            mpesa_code = match.group(1)
            amount = float(match.group(2).replace(",", ""))
            phone = match.group(3)
            date_str = match.group(4) + " " + match.group(5)

            date_obj = datetime.strptime(date_str, "%d/%m/%y %I:%M %p")

        except Exception as e:
            return Response({"detail": f"Parsing error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # ------------------------------------
        # 3. DUPLICATE CHECK
        # ------------------------------------
        if Transaction.objects.filter(mpesa_code=mpesa_code).exists():
            return Response(
                {"detail": "Duplicate transaction", "mpesa_code": mpesa_code},
                status=status.HTTP_409_CONFLICT
            )

        # ------------------------------------
        # 4. SAVE TRANSACTION
        # ------------------------------------
        tx = Transaction.objects.create(
            mpesa_code=mpesa_code,
            amount=amount,
            phone=phone,
            date=date_obj,
            raw_message=text,
            username=username,
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
