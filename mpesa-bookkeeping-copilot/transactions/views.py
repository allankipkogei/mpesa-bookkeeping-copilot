from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.utils import timezone
import csv, io, dateutil.parser

from .models import Transaction
from .serializers import TransactionSerializer

class TransactionListCreateView(generics.ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by("-date")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # ensure users can only see their own transactions
        return Transaction.objects.filter(user=self.request.user)


class UploadStatementView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        """
        Accepts a CSV or TXT file upload with columns:
        amount,mpesa_code,date,trans_type,phone_number,category (date ISO or dd/mm/yyyy)
        """
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

        decoded = file_obj.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))
        created = 0
        errors = []
        for i, row in enumerate(reader, start=1):
            try:
                amount = row.get("amount") or row.get("Amount")
                amount = float(amount.replace(",", "")) if amount else 0.0

                mpesa_code = (row.get("mpesa_code") or row.get("MpesaCode") or row.get("code") or "").strip()
                date_str = row.get("date") or row.get("Date") or ""
                if date_str:
                    try:
                        date = dateutil.parser.parse(date_str)
                    except Exception:
                        date = timezone.now()
                else:
                    date = timezone.now()

                trans_type = (row.get("trans_type") or row.get("type") or "C2B").upper()
                phone_number = row.get("phone_number") or row.get("phone") or ""
                category = row.get("category") or ""

                # skip if no mpesa_code or amount
                if not mpesa_code:
                    errors.append({"row": i, "error": "missing mpesa_code"})
                    continue

                # Create if not exists
                obj, created_flag = Transaction.objects.get_or_create(
                    user=request.user,
                    mpesa_code=mpesa_code,
                    defaults={
                        "amount": amount,
                        "trans_type": trans_type,
                        "phone_number": phone_number,
                        "date": date,
                        "category": category,
                    },
                )
                if created_flag:
                    created += 1
            except Exception as e:
                errors.append({"row": i, "error": str(e)})

        return Response({"created": created, "errors": errors})
