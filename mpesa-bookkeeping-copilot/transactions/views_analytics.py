"""
Analytics views for dashboard insights and reporting.
Provides monthly trends, category analysis, cashflow, and recurring payments detection.
"""

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth, TruncDay, TruncWeek
from django.utils.timezone import now
from datetime import timedelta, datetime
from collections import defaultdict
import re

from django.contrib.auth import get_user_model
from transactions.models import Transaction

User = get_user_model()


class MonthlyAnalyticsView(views.APIView):
    """
    Monthly transaction analytics with income, expenses, and trends.
    GET /api/analytics/monthly/?months=6
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get number of months to analyze (default: 6)
        months = int(request.query_params.get('months', 6))
        
        # Calculate date range
        end_date = now()
        start_date = end_date - timedelta(days=months * 30)
        
        # Get transactions grouped by month
        monthly_data = Transaction.objects.filter(
            date__gte=start_date
        ).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total_income=Sum('amount', filter=Q(trans_type='C2B')),
            total_expenses=Sum('amount', filter=~Q(trans_type='C2B')),
            transaction_count=Count('id'),
            avg_transaction=Avg('amount')
        ).order_by('month')
        
        # Format response
        formatted_data = []
        for item in monthly_data:
            income = float(item['total_income'] or 0)
            expenses = float(item['total_expenses'] or 0)
            net_cashflow = income - expenses
            
            formatted_data.append({
                'month': item['month'].strftime('%Y-%m'),
                'month_name': item['month'].strftime('%B %Y'),
                'total_income': income,
                'total_expenses': expenses,
                'net_cashflow': net_cashflow,
                'transaction_count': item['transaction_count'],
                'avg_transaction': float(item['avg_transaction'] or 0)
            })
        
        # Calculate overall statistics
        total_income = sum(item['total_income'] for item in formatted_data)
        total_expenses = sum(item['total_expenses'] for item in formatted_data)
        
        return Response({
            'monthly_data': formatted_data,
            'summary': {
                'total_income': total_income,
                'total_expenses': total_expenses,
                'net_balance': total_income - total_expenses,
                'months_analyzed': len(formatted_data),
                'avg_monthly_income': total_income / len(formatted_data) if formatted_data else 0,
                'avg_monthly_expenses': total_expenses / len(formatted_data) if formatted_data else 0
            }
        })


class TopCategoriesView(views.APIView):
    """
    Top spending categories with trends and comparisons.
    GET /api/analytics/top-categories/?limit=10&period=30
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get parameters
        limit = int(request.query_params.get('limit', 10))
        period_days = int(request.query_params.get('period', 30))
        
        # Calculate date range
        end_date = now()
        start_date = end_date - timedelta(days=period_days)
        
        # Get category statistics
        category_stats = Transaction.objects.filter(
            date__gte=start_date,
            category__isnull=False
        ).exclude(
            category=''
        ).values('category').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id'),
            avg_amount=Avg('amount')
        ).order_by('-total_amount')[:limit]
        
        # Format response
        formatted_stats = []
        total_spending = Transaction.objects.filter(
            date__gte=start_date
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        for stat in category_stats:
            amount = float(stat['total_amount'])
            percentage = (amount / float(total_spending) * 100) if total_spending > 0 else 0
            
            formatted_stats.append({
                'category': stat['category'],
                'total_amount': amount,
                'transaction_count': stat['transaction_count'],
                'avg_amount': float(stat['avg_amount']),
                'percentage_of_total': round(percentage, 2)
            })
        
        return Response({
            'top_categories': formatted_stats,
            'period_days': period_days,
            'total_spending': float(total_spending)
        })


class CashflowView(views.APIView):
    """
    Daily/Weekly cashflow analysis showing money in vs money out.
    GET /api/analytics/cashflow/?period=30&granularity=daily
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get parameters
        period_days = int(request.query_params.get('period', 30))
        granularity = request.query_params.get('granularity', 'daily')  # daily, weekly
        
        # Calculate date range
        end_date = now()
        start_date = end_date - timedelta(days=period_days)
        
        # Choose aggregation function
        trunc_func = TruncDay if granularity == 'daily' else TruncWeek
        
        # Get cashflow data
        cashflow_data = Transaction.objects.filter(
            date__gte=start_date
        ).annotate(
            period=trunc_func('date')
        ).values('period').annotate(
            money_in=Sum('amount', filter=Q(trans_type='C2B')),
            money_out=Sum('amount', filter=~Q(trans_type='C2B')),
            transaction_count=Count('id')
        ).order_by('period')
        
        # Format response with running balance
        formatted_data = []
        running_balance = 0
        
        for item in cashflow_data:
            money_in = float(item['money_in'] or 0)
            money_out = float(item['money_out'] or 0)
            net_flow = money_in - money_out
            running_balance += net_flow
            
            formatted_data.append({
                'date': item['period'].strftime('%Y-%m-%d'),
                'money_in': money_in,
                'money_out': money_out,
                'net_flow': net_flow,
                'running_balance': running_balance,
                'transaction_count': item['transaction_count']
            })
        
        # Calculate summary statistics
        total_in = sum(item['money_in'] for item in formatted_data)
        total_out = sum(item['money_out'] for item in formatted_data)
        
        # Identify best and worst days
        best_day = max(formatted_data, key=lambda x: x['net_flow']) if formatted_data else None
        worst_day = min(formatted_data, key=lambda x: x['net_flow']) if formatted_data else None
        
        return Response({
            'cashflow_data': formatted_data,
            'summary': {
                'total_money_in': total_in,
                'total_money_out': total_out,
                'net_cashflow': total_in - total_out,
                'final_balance': running_balance,
                'best_day': best_day,
                'worst_day': worst_day,
                'period_days': period_days,
                'granularity': granularity
            }
        })


class RecurringPaymentsView(views.APIView):
    """
    Detect and analyze recurring payments based on patterns.
    GET /api/analytics/recurring-payments/?min_occurrences=2
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get parameters
        min_occurrences = int(request.query_params.get('min_occurrences', 2))
        lookback_days = int(request.query_params.get('lookback_days', 90))
        
        # Calculate date range
        end_date = now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Get all transactions
        transactions = Transaction.objects.filter(
            date__gte=start_date
        ).exclude(
            trans_type='C2B'  # Exclude income
        ).order_by('date')
        
        # Group by similar characteristics
        payment_patterns = defaultdict(list)
        
        for tx in transactions:
            # Create a key based on amount, phone number, and description pattern
            amount_rounded = round(float(tx.amount) / 100) * 100  # Round to nearest 100
            description_clean = self._clean_description(tx.description or '')
            
            key = (
                amount_rounded,
                tx.phone_number or 'unknown',
                description_clean,
                tx.category or 'uncategorized'
            )
            
            payment_patterns[key].append({
                'id': tx.pk,
                'date': tx.date,
                'amount': float(tx.amount),
                'mpesa_code': tx.mpesa_code,
                'description': tx.description or ''
            })
        
        # Identify recurring patterns
        recurring_payments = []
        
        for key, transactions_list in payment_patterns.items():
            if len(transactions_list) >= min_occurrences:
                amount_rounded, phone, desc_pattern, category = key
                
                # Calculate frequency
                dates = [tx['date'] for tx in transactions_list]
                dates.sort()
                
                # Calculate average interval between payments
                intervals = []
                for i in range(1, len(dates)):
                    interval = (dates[i] - dates[i-1]).days
                    intervals.append(interval)
                
                avg_interval = sum(intervals) / len(intervals) if intervals else 0
                
                # Determine frequency type
                frequency = self._determine_frequency(avg_interval)
                
                recurring_payments.append({
                    'pattern_id': hash(key),
                    'description_pattern': desc_pattern,
                    'phone_number': phone,
                    'category': category,
                    'approximate_amount': amount_rounded,
                    'occurrence_count': len(transactions_list),
                    'avg_interval_days': round(avg_interval, 1),
                    'frequency': frequency,
                    'total_spent': sum(tx['amount'] for tx in transactions_list),
                    'first_occurrence': dates[0].strftime('%Y-%m-%d'),
                    'last_occurrence': dates[-1].strftime('%Y-%m-%d'),
                    'transactions': transactions_list
                })
        
        # Sort by total spent
        recurring_payments.sort(key=lambda x: x['total_spent'], reverse=True)
        
        # Calculate summary
        total_recurring_spending = sum(p['total_spent'] for p in recurring_payments)
        
        return Response({
            'recurring_payments': recurring_payments,
            'summary': {
                'total_patterns_found': len(recurring_payments),
                'total_recurring_spending': total_recurring_spending,
                'lookback_days': lookback_days,
                'min_occurrences': min_occurrences
            }
        })
    
    def _clean_description(self, description):
        """Clean and normalize description for pattern matching"""
        if not description:
            return 'no_description'
        
        # Remove codes, numbers, dates
        cleaned = re.sub(r'[A-Z0-9]{8,}', '', description)  # Remove codes
        cleaned = re.sub(r'\d{10,}', '', cleaned)  # Remove long numbers
        cleaned = re.sub(r'\d+/\d+/\d+', '', cleaned)  # Remove dates
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize spaces
        
        # Extract key words (first 3 significant words)
        words = [w for w in cleaned.lower().split() if len(w) > 3][:3]
        
        return ' '.join(words) if words else 'generic'
    
    def _determine_frequency(self, avg_interval):
        """Determine payment frequency based on average interval"""
        if avg_interval <= 1:
            return 'daily'
        elif avg_interval <= 7:
            return 'weekly'
        elif avg_interval <= 14:
            return 'bi-weekly'
        elif avg_interval <= 31:
            return 'monthly'
        elif avg_interval <= 92:
            return 'quarterly'
        else:
            return 'irregular'


class SpendingTrendsView(views.APIView):
    """
    Analyze spending trends and provide insights.
    GET /api/analytics/spending-trends/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get last 30 days and previous 30 days
        end_date = now()
        current_period_start = end_date - timedelta(days=30)
        previous_period_start = current_period_start - timedelta(days=30)
        
        # Current period stats
        current_stats = Transaction.objects.filter(
            date__gte=current_period_start
        ).aggregate(
            total_spending=Sum('amount', filter=~Q(trans_type='C2B')),
            total_income=Sum('amount', filter=Q(trans_type='C2B')),
            transaction_count=Count('id')
        )
        
        # Previous period stats
        previous_stats = Transaction.objects.filter(
            date__gte=previous_period_start,
            date__lt=current_period_start
        ).aggregate(
            total_spending=Sum('amount', filter=~Q(trans_type='C2B')),
            total_income=Sum('amount', filter=Q(trans_type='C2B')),
            transaction_count=Count('id')
        )
        
        # Calculate changes
        current_spending = float(current_stats['total_spending'] or 0)
        previous_spending = float(previous_stats['total_spending'] or 0)
        spending_change = ((current_spending - previous_spending) / previous_spending * 100) if previous_spending > 0 else 0
        
        current_income = float(current_stats['total_income'] or 0)
        previous_income = float(previous_stats['total_income'] or 0)
        income_change = ((current_income - previous_income) / previous_income * 100) if previous_income > 0 else 0
        
        # Category trends
        category_trends = []
        categories = Transaction.objects.filter(
            date__gte=previous_period_start,
            category__isnull=False
        ).exclude(category='').values_list('category', flat=True).distinct()
        
        for category in categories:
            current_amount = Transaction.objects.filter(
                date__gte=current_period_start,
                category=category
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            previous_amount = Transaction.objects.filter(
                date__gte=previous_period_start,
                date__lt=current_period_start,
                category=category
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            change = ((float(current_amount) - float(previous_amount)) / float(previous_amount) * 100) if previous_amount > 0 else 0
            
            category_trends.append({
                'category': category,
                'current_amount': float(current_amount),
                'previous_amount': float(previous_amount),
                'change_percentage': round(change, 2),
                'trend': 'increasing' if change > 5 else 'decreasing' if change < -5 else 'stable'
            })
        
        # Sort by absolute change
        category_trends.sort(key=lambda x: abs(x['change_percentage']), reverse=True)
        
        return Response({
            'current_period': {
                'spending': current_spending,
                'income': current_income,
                'transaction_count': current_stats['transaction_count']
            },
            'previous_period': {
                'spending': previous_spending,
                'income': previous_income,
                'transaction_count': previous_stats['transaction_count']
            },
            'changes': {
                'spending_change_percentage': round(spending_change, 2),
                'income_change_percentage': round(income_change, 2),
                'spending_trend': 'increasing' if spending_change > 5 else 'decreasing' if spending_change < -5 else 'stable',
                'income_trend': 'increasing' if income_change > 5 else 'decreasing' if income_change < -5 else 'stable'
            },
            'category_trends': category_trends[:10]  # Top 10 categories by change
        })


class BudgetInsightsView(views.APIView):
    """
    Provide budget insights and recommendations.
    GET /api/analytics/budget-insights/
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Analyze last 30 days
        end_date = now()
        start_date = end_date - timedelta(days=30)
        
        # Category spending
        category_spending = Transaction.objects.filter(
            date__gte=start_date,
            category__isnull=False
        ).exclude(
            category='',
            trans_type='C2B'
        ).values('category').annotate(
            total=Sum('amount')
        )
        
        total_spending = sum(float(c['total']) for c in category_spending)
        
        # Calculate recommended budgets (based on common percentages)
        recommended_percentages = {
            'Food': 0.25,
            'Transport': 0.15,
            'Utilities': 0.15,
            'Personal': 0.10,
            'Business Expenses': 0.20,
            'Inventory': 0.15
        }
        
        insights = []
        for cat_data in category_spending:
            category = cat_data['category']
            actual_amount = float(cat_data['total'])
            actual_percentage = (actual_amount / total_spending * 100) if total_spending > 0 else 0
            
            recommended_pct = recommended_percentages.get(category, 0.10) * 100
            recommended_amount = total_spending * recommended_percentages.get(category, 0.10)
            
            variance = actual_amount - recommended_amount
            status = 'over_budget' if variance > 0 else 'under_budget' if variance < -recommended_amount * 0.1 else 'on_track'
            
            insights.append({
                'category': category,
                'actual_spending': actual_amount,
                'actual_percentage': round(actual_percentage, 2),
                'recommended_percentage': round(recommended_pct, 2),
                'recommended_amount': round(recommended_amount, 2),
                'variance': round(variance, 2),
                'status': status
            })
        
        return Response({
            'budget_insights': insights,
            'total_spending': total_spending,
            'period_days': 30
        })
