from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.timezone import now
from django.db.models import Sum, Count
from django.db.models.functions import TruncDay

import csv
import io
import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from .models import Transaction
from .serializers import TransactionSerializer
from .utils.mpesa_parser import MPesaParser
from .utils.categorizer import TransactionCategorizer

# For PDF processing
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

User = get_user_model()


# ----------------------------------------------------
# LIST + CREATE TRANSACTIONS
# ----------------------------------------------------
class TransactionListCreateView(generics.ListCreateAPIView):
    queryset = Transaction.objects.all().order_by("-date")
    serializer_class = TransactionSerializer


# ----------------------------------------------------
# SINGLE TRANSACTION DETAIL
# ----------------------------------------------------
class TransactionDetailView(generics.RetrieveAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


# ----------------------------------------------------
# TRANSACTION SUMMARY (TOTALS + WEEKLY ANALYTICS)
# ----------------------------------------------------
class TransactionSummaryView(views.APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        qs = Transaction.objects.all()

        # Totals
        total_amount = qs.aggregate(total_amount=Sum("amount"))["total_amount"] or 0
        total_transactions = qs.count()
        today_total = (
            qs.filter(date__date=now().date())
              .aggregate(total=Sum("amount"))["total"]
            or 0
        )

        # Weekly analytics (last 7 days)
        week_ago = now() - timedelta(days=7)
        weekly_data = (
            qs.filter(date__gte=week_ago)
              .annotate(day=TruncDay("date"))
              .values("day")
              .annotate(
                  total=Sum("amount"),
                  count=Count("id"),
              )
              .order_by("day")
        )

        return Response({
            "total_amount": total_amount,
            "total_transactions": total_transactions,
            "today_total": today_total,
            "weekly_data": list(weekly_data),
        })


# ----------------------------------------------------
# UPLOAD TRANSACTION STATEMENT (CSV / PDF / SMS)
# ----------------------------------------------------
class UploadStatementView(views.APIView):
    """
    Upload M-Pesa statements in multiple formats:
    - CSV: M-Pesa statement CSV export
    - PDF: M-Pesa statement PDF (requires PyPDF2)
    - TXT/SMS: Plain text SMS exports
    
    Automatically detects format and extracts transactions.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        file = request.FILES.get("file")
        file_type = request.data.get("type", "auto")  # auto, csv, pdf, sms
        user_id = request.data.get("user_id")
        
        if not file:
            return Response(
                {"detail": "No file uploaded"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create default user if not specified
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {"detail": f"User with ID {user_id} not found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Use first user or create one
            user = User.objects.first()
            if not user:
                return Response(
                    {"detail": "No users found. Please create a user first."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Auto-detect file type from extension if not specified
        if file_type == "auto":
            filename = file.name.lower()
            if filename.endswith('.csv'):
                file_type = "csv"
            elif filename.endswith('.pdf'):
                file_type = "pdf"
            elif filename.endswith('.txt') or filename.endswith('.sms'):
                file_type = "sms"
            else:
                file_type = "csv"  # Default to CSV
        
        created = 0
        skipped = 0
        errors = []
        transactions_data = []
        
        try:
            # Process based on file type
            if file_type == "csv":
                transactions_data = self._process_csv(file)
            elif file_type == "pdf":
                if not PDF_SUPPORT:
                    return Response(
                        {"detail": "PDF support not installed. Install PyPDF2 package."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                transactions_data = self._process_pdf(file)
            elif file_type == "sms":
                transactions_data = self._process_sms(file)
            else:
                return Response(
                    {"detail": f"Unsupported file type: {file_type}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create transactions in database
            for tx_data in transactions_data:
                if not tx_data:
                    continue
                
                try:
                    # Check if transaction already exists
                    existing = Transaction.objects.filter(
                        mpesa_code=tx_data["mpesa_code"]
                    ).first()
                    
                    if existing:
                        skipped += 1
                        continue
                    
                    # Auto-categorize transaction
                    categorization = TransactionCategorizer.categorize(
                        description=tx_data.get("description", ""),
                        trans_type=tx_data.get("trans_type", "C2B"),
                        phone_number=tx_data.get("phone_number", ""),
                        amount=tx_data.get("amount", 0)
                    )
                    
                    # Create new transaction with auto-category
                    Transaction.objects.create(
                        user=user,
                        mpesa_code=tx_data["mpesa_code"],
                        amount=tx_data["amount"],
                        trans_type=tx_data.get("trans_type", "C2B"),
                        phone_number=tx_data.get("phone_number", ""),
                        date=tx_data.get("date", now()),
                        description=tx_data.get("description", ""),
                        category=categorization["category"]
                    )
                    created += 1
                    
                except Exception as e:
                    errors.append({
                        "mpesa_code": tx_data.get("mpesa_code", "Unknown"),
                        "error": str(e)
                    })
            
            return Response({
                "success": True,
                "created_transactions": created,
                "skipped_duplicates": skipped,
                "total_processed": len(transactions_data),
                "errors": errors[:10],  # Limit error messages
                "file_type": file_type
            })
            
        except Exception as e:
            return Response(
                {"detail": f"Error processing file: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _process_csv(self, file):
        """Process CSV file and extract transactions"""
        transactions = []
        try:
            decoded_file = file.read().decode("utf-8")
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            for row in reader:
                tx_data = MPesaParser.parse_csv_row(row)
                if tx_data:
                    transactions.append(tx_data)
        except Exception as e:
            print(f"CSV processing error: {e}")
        
        return transactions
    
    def _process_pdf(self, file):
        """Process PDF file and extract transactions"""
        transactions = []
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            full_text = ""
            
            for page in pdf_reader.pages:
                full_text += page.extract_text() + "\n"
            
            transactions = MPesaParser.parse_pdf_text(full_text)
        except Exception as e:
            print(f"PDF processing error: {e}")
        
        return transactions
    
    def _process_sms(self, file):
        """Process SMS text file and extract transactions"""
        transactions = []
        try:
            decoded_file = file.read().decode("utf-8")
            
            # Split by common SMS separators
            sms_messages = re.split(r'\n\n+|\r\n\r\n+', decoded_file)
            
            for sms in sms_messages:
                tx_data = MPesaParser.parse_sms(sms.strip())
                if tx_data:
                    transactions.append(tx_data)
        except Exception as e:
            print(f"SMS processing error: {e}")
        
        return transactions


# ----------------------------------------------------
# AI CATEGORIZATION ENDPOINTS
# ----------------------------------------------------
class CategorizeTransactionView(views.APIView):
    """
    Manually trigger categorization for a specific transaction.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, pk):
        try:
            transaction = Transaction.objects.get(pk=pk)
        except Transaction.DoesNotExist:
            return Response(
                {"detail": "Transaction not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Categorize transaction
        categorization = TransactionCategorizer.categorize(
            description=transaction.description or "",
            trans_type=transaction.trans_type,
            phone_number=transaction.phone_number or "",
            amount=float(transaction.amount)
        )
        
        # Update transaction
        transaction.category = categorization["category"]
        transaction.save()
        
        return Response({
            "transaction_id": transaction.id,
            "mpesa_code": transaction.mpesa_code,
            "category": categorization["category"],
            "confidence": categorization["confidence"],
            "reasoning": categorization["reasoning"]
        })


class BulkCategorizeView(views.APIView):
    """
    Categorize all uncategorized transactions.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Get uncategorized or incorrectly categorized transactions
        transactions = Transaction.objects.filter(
            category__isnull=True
        ) | Transaction.objects.filter(category="")
        
        categorized_count = 0
        
        for transaction in transactions:
            categorization = TransactionCategorizer.categorize(
                description=transaction.description or "",
                trans_type=transaction.trans_type,
                phone_number=transaction.phone_number or "",
                amount=float(transaction.amount)
            )
            
            transaction.category = categorization["category"]
            transaction.save()
            categorized_count += 1
        
        return Response({
            "success": True,
            "categorized_count": categorized_count,
            "message": f"Successfully categorized {categorized_count} transactions"
        })


class CategorySuggestionsView(views.APIView):
    """
    Get category suggestions for a given description.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        description = request.data.get("description", "")
        
        if not description:
            return Response(
                {"detail": "Description is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        suggestions = TransactionCategorizer.suggest_category(description)
        
        return Response({
            "description": description,
            "suggestions": suggestions
        })


class CategoryListView(views.APIView):
    """
    Get list of all available categories.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        categories = TransactionCategorizer.get_categories()
        
        return Response({
            "categories": categories
        })


class CategoryStatsView(views.APIView):
    """
    Get spending statistics by category.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get all transactions grouped by category
        category_stats = Transaction.objects.values('category').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')
        
        # Calculate percentages
        total_amount = Transaction.objects.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        stats_with_percentage = []
        for stat in category_stats:
            percentage = (float(stat['total_amount']) / float(total_amount) * 100) if total_amount > 0 else 0
            stats_with_percentage.append({
                'category': stat['category'] or 'Uncategorized',
                'total_amount': float(stat['total_amount']),
                'transaction_count': stat['transaction_count'],
                'percentage': round(percentage, 2)
            })
        
        return Response({
            "category_stats": stats_with_percentage,
            "total_amount": float(total_amount)
        })


class UpdateTransactionCategoryView(views.APIView):
    """
    Manually update a transaction's category.
    """
    permission_classes = [AllowAny]
    
    def patch(self, request, pk):
        try:
            transaction = Transaction.objects.get(pk=pk)
        except Transaction.DoesNotExist:
            return Response(
                {"detail": "Transaction not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_category = request.data.get("category")
        
        if not new_category:
            return Response(
                {"detail": "Category is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate category
        valid_categories = TransactionCategorizer.get_categories()
        if new_category not in valid_categories:
            return Response(
                {"detail": f"Invalid category. Valid categories: {', '.join(valid_categories)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transaction.category = new_category
        transaction.save()
        
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)
