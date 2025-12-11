# AI Auto-Categorization Feature

## Overview
The M-Pesa Bookkeeping system now includes intelligent auto-categorization of transactions using pattern matching and keyword analysis.

## Supported Categories

### 1. **Food**
- Restaurants, cafes, coffee shops
- Grocery stores, supermarkets
- Fast food chains (KFC, Subway, Domino's, etc.)
- Local stores (Naivas, Carrefour, Quickmart, etc.)

### 2. **Transport**
- Ride-hailing (Uber, Bolt, Little Cab)
- Taxi and matatu fares
- Fuel purchases (Total, Shell, Kenol)
- Parking and toll fees

### 3. **Inventory**
- Stock purchases
- Wholesale suppliers
- Merchandise and goods
- Raw materials and procurement

### 4. **Personal**
- Clothing and fashion
- Entertainment (movies, cinema)
- Gym and fitness
- Salon, beauty, spa services
- Personal shopping and gifts

### 5. **Utilities**
- Electricity (KPLC)
- Water bills
- Internet and mobile data (Safaricom, Airtel, Telkom)
- Rent payments

### 6. **Business Expenses**
- Office supplies and stationery
- Marketing and advertising
- Legal and accounting services
- Software subscriptions
- Professional services
- Business licenses and permits

### 7. **Income**
- Money received (C2B transactions)
- Customer payments

### 8. **Uncategorized**
- Transactions that don't match any category

## How It Works

### Automatic Categorization
When you upload a statement (CSV, PDF, or SMS), the system:
1. Parses the transaction details
2. Analyzes the description text
3. Matches keywords and patterns
4. Assigns the most appropriate category
5. Calculates a confidence score

### API Endpoints

#### 1. Auto-Categorize Single Transaction
```http
POST /api/transactions/{id}/categorize/
```
Manually trigger categorization for a specific transaction.

**Response:**
```json
{
  "transaction_id": 1,
  "mpesa_code": "SLK1A2B3C4",
  "category": "Food",
  "confidence": 0.8,
  "reasoning": "Matched keywords in description"
}
```

#### 2. Bulk Categorize All Transactions
```http
POST /api/transactions/bulk-categorize/
```
Categorize all uncategorized transactions at once.

**Response:**
```json
{
  "success": true,
  "categorized_count": 25,
  "message": "Successfully categorized 25 transactions"
}
```

#### 3. Get Category Suggestions
```http
POST /api/transactions/category-suggestions/
```
Get top 3 category suggestions for a description.

**Request Body:**
```json
{
  "description": "Bought coffee at Java House"
}
```

**Response:**
```json
{
  "description": "Bought coffee at Java House",
  "suggestions": [
    {
      "category": "Food",
      "confidence": 0.9,
      "score": 9
    },
    {
      "category": "Personal",
      "confidence": 0.3,
      "score": 3
    }
  ]
}
```

#### 4. List All Categories
```http
GET /api/transactions/categories/
```
Get list of all available categories.

**Response:**
```json
{
  "categories": [
    "Food",
    "Transport",
    "Inventory",
    "Personal",
    "Utilities",
    "Business Expenses",
    "Income",
    "Uncategorized",
    "Other"
  ]
}
```

#### 5. Get Category Statistics
```http
GET /api/transactions/category-stats/
```
Get spending breakdown by category.

**Response:**
```json
{
  "category_stats": [
    {
      "category": "Food",
      "total_amount": 15000.00,
      "transaction_count": 12,
      "percentage": 25.5
    },
    {
      "category": "Transport",
      "total_amount": 8500.00,
      "transaction_count": 8,
      "percentage": 14.5
    }
  ],
  "total_amount": 58750.00
}
```

#### 6. Update Transaction Category
```http
PATCH /api/transactions/{id}/category/
```
Manually change a transaction's category.

**Request Body:**
```json
{
  "category": "Food"
}
```

## Frontend Features

### 1. Transactions Table
- Displays category badges with color coding
- Each category has a unique color for easy identification

### 2. Category Statistics Dashboard
- Pie chart showing spending distribution
- List view with percentages and amounts
- Transaction counts per category

### 3. Bulk Categorization Button
- One-click categorization of all uncategorized transactions
- Shows progress and completion status

## Usage Examples

### Python API Usage
```python
from transactions.utils.categorizer import TransactionCategorizer

# Categorize a single transaction
result = TransactionCategorizer.categorize(
    description="Paid for lunch at Java House",
    trans_type="B2C",
    phone_number="254712345678",
    amount=850.00
)
print(result)
# Output: {'category': 'Food', 'confidence': 0.9, 'reasoning': 'Matched keywords in description'}

# Get category suggestions
suggestions = TransactionCategorizer.suggest_category(
    "Bought groceries at Carrefour"
)
print(suggestions)
# Output: [{'category': 'Food', 'confidence': 0.8, 'score': 8}]

# Bulk categorize transactions
transactions = [
    {"description": "Uber ride", "trans_type": "B2C", "amount": 500},
    {"description": "KPLC token", "trans_type": "PAYBILL", "amount": 2000}
]
categorized = TransactionCategorizer.bulk_categorize(transactions)
```

### JavaScript/React Usage
```javascript
import axios from 'axios';

// Bulk categorize all transactions
const categorizeAll = async () => {
  const response = await axios.post(
    'http://127.0.0.1:8000/api/transactions/bulk-categorize/'
  );
  console.log(response.data.message);
};

// Get category statistics
const getStats = async () => {
  const response = await axios.get(
    'http://127.0.0.1:8000/api/transactions/category-stats/'
  );
  console.log(response.data.category_stats);
};

// Update transaction category
const updateCategory = async (transactionId, category) => {
  await axios.patch(
    `http://127.0.0.1:8000/api/transactions/${transactionId}/category/`,
    { category }
  );
};
```

## Testing

### Test with Sample Data
1. Upload the provided `sample_data/mpesa_statement_sample.csv`
2. Transactions will be automatically categorized
3. Check the Transactions page to see categories
4. View Category Statistics dashboard

### Expected Results
- Coffee shop → **Food**
- Uber ride → **Transport**
- Grocery shopping → **Food**
- Office supplies → **Business Expenses**
- KPLC payment → **Utilities**
- KFC meal → **Food**
- Internet bundle → **Utilities**
- Wholesale stock → **Inventory**
- Salon treatment → **Personal**
- Customer payment → **Income**

## Customization

To add new categories or keywords, edit `transactions/utils/categorizer.py`:

```python
CATEGORIES = {
    "Your New Category": {
        "keywords": ["keyword1", "keyword2", "keyword3"],
        "patterns": [r"regex_pattern1", r"regex_pattern2"]
    }
}
```

## Best Practices

1. **Upload with Descriptions**: Ensure transaction descriptions are included for best categorization results
2. **Review Categories**: Periodically review auto-categorized transactions
3. **Manual Correction**: Use the update category endpoint to correct miscategorized transactions
4. **Regular Updates**: Keep keyword lists updated with new merchants and services

## Troubleshooting

### Low Confidence Scores
- Add more specific keywords to the category
- Improve transaction descriptions during upload

### Wrong Categories
- Use the manual category update endpoint
- Add negative patterns to exclude certain keywords

### Uncategorized Transactions
- Click "Auto-Categorize All" button to retry
- Manually assign categories using the API
- Add missing keywords to the categorizer

## Future Enhancements

- [ ] Machine learning-based categorization
- [ ] Custom user-defined categories
- [ ] Subcategory support
- [ ] Historical category patterns
- [ ] Smart category suggestions based on past behavior
- [ ] Export category reports
