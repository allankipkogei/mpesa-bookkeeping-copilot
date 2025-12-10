from django.db import models
from django.conf import settings
from django.utils import timezone  # <-- import timezone

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("C2B", "Customer to Business"),
        ("B2C", "Business to Customer"),
        ("PAYBILL", "Paybill"),
        ("BUYGOODS", "Buy Goods"),
        ("P2P", "Person to Person"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trans_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    mpesa_code = models.CharField(max_length=50, unique=True)
    date = models.DateTimeField(default=timezone.now)  # <-- add default
    category = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.mpesa_code} - {self.amount}"
