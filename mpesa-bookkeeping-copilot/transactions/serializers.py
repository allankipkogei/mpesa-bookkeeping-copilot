from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "user",
            "trans_type",
            "amount",
            "phone_number",
            "mpesa_code",
            "date",
            "category",
            "description",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
