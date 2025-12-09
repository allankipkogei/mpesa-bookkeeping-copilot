from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("mpesa_code", "user", "amount", "trans_type", "date", "category")
    search_fields = ("mpesa_code", "phone_number", "category")
    list_filter = ("trans_type", "category")
