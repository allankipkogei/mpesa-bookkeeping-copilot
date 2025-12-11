# M-Pesa Statement Upload Feature

## Overview
This feature allows you to automatically extract M-Pesa transactions from multiple file formats:
- **CSV** - M-Pesa statement CSV exports
- **PDF** - M-Pesa statement PDF files
- **SMS/TXT** - Plain text SMS exports

## Backend Implementation

### API Endpoint
**POST** `/api/transactions/upload/`

### Request Parameters
- `file` (required): The file to upload (CSV, PDF, or TXT)
- `type` (optional): File type - `auto`, `csv`, `pdf`, or `sms`. Default: `auto` (auto-detects from extension)
- `user_id` (optional): User ID to associate transactions with. Uses first user if not provided.

### Response Format
```json
{
  "success": true,
  "created_transactions": 10,
  "skipped_duplicates": 2,
  "total_processed": 12,
  "errors": [],
  "file_type": "csv"
}
```

### Parser Capabilities

#### CSV Parser
Supports M-Pesa CSV formats with columns:
- Receipt No / Transaction ID
- Completion Time / Date
- Details / Description
- Paid In / Withdrawn / Amount
- Other Party Info / Phone Number

#### PDF Parser
Extracts transaction data from M-Pesa PDF statements by:
- Reading PDF text content
- Identifying transaction patterns
- Parsing amounts, dates, and transaction codes

#### SMS Parser
Recognizes multiple M-Pesa SMS formats:
- Money received: `"received Ksh X from Y"`
- Money sent: `"sent Ksh X to Y"`
- Withdrawals: `"withdrew Ksh X from Y"`
- Paybill/Buy Goods transactions

### Features
- ✅ Automatic duplicate detection (by M-Pesa code)
- ✅ Multiple date format support
- ✅ Transaction type auto-detection (C2B/B2C)
- ✅ Phone number extraction
- ✅ Error handling and reporting

## Frontend Implementation

### Upload Component
Location: `src/components/UploadStatement.jsx`

Features:
- Drag & drop or file selection
- Auto-detection of file type
- Manual file type override
- Real-time upload progress
- Success/error feedback
- Upload statistics display

### Transactions Page
Location: `src/pages/Transactions.jsx`

Features:
- Upload form integration
- Transaction list display
- Auto-refresh after upload

## Installation

### Backend Dependencies
```bash
cd mpesa-bookkeeping-copilot
pip install -r requirements.txt
```

Required packages:
- `PyPDF2>=3.0.0` - PDF processing

### Frontend
No additional dependencies required. Uses existing axios for API calls.

## Usage

### 1. Start the Backend
```bash
cd mpesa-bookkeeping-copilot
python manage.py runserver
```

### 2. Start the Frontend
```bash
cd mpesa-dashboard
npm run dev
```

### 3. Upload a Statement
1. Navigate to `/transactions` page
2. Click "Choose File" and select your M-Pesa statement
3. Choose file type (or use auto-detect)
4. Click "Upload Statement"
5. View results and newly imported transactions

## Sample Files

Sample files are provided in `sample_data/`:
- `mpesa_statement_sample.csv` - Sample CSV with 10 transactions
- `mpesa_sms_sample.txt` - Sample SMS exports with various transaction types

## Testing

### Test CSV Upload
```bash
curl -X POST http://127.0.0.1:8000/api/transactions/upload/ \
  -F "file=@sample_data/mpesa_statement_sample.csv" \
  -F "type=csv"
```

### Test SMS Upload
```bash
curl -X POST http://127.0.0.1:8000/api/transactions/upload/ \
  -F "file=@sample_data/mpesa_sms_sample.txt" \
  -F "type=sms"
```

## Supported M-Pesa SMS Formats

### Received Money
```
SLK1A2B3C4 Confirmed. You have received Ksh 5,000.00 from John Doe 254712345678 on 12/1/25 at 9:15 AM
```

### Sent Money
```
SLK2B3C4D5 Confirmed. You have sent Ksh 2,000.00 to Jane Smith 254723456789 on 12/2/25 at 10:30 AM
```

### Withdrawal
```
SLK3C4D5E6 Confirmed. You have withdrawn Ksh 1,500.00 from M-PESA Agent on 12/3/25 at 11:20 AM
```

### Paybill/Buy Goods
```
SLK4D5E6F7 Confirmed. You have paid Ksh 850.50 for goods at ABC Store on 12/4/25 at 9:50 AM
```

## Error Handling

The system handles:
- Invalid file formats
- Corrupt or unreadable files
- Duplicate transactions (skips automatically)
- Missing or invalid data fields
- PDF parsing failures
- Date format variations

## Future Enhancements

Potential improvements:
- [ ] Bank statement integration
- [ ] Excel file support
- [ ] Image/screenshot OCR
- [ ] Bulk upload (multiple files)
- [ ] Transaction categorization
- [ ] Expense analytics
- [ ] Export processed data

## Troubleshooting

### PDF Upload Fails
Ensure PyPDF2 is installed:
```bash
pip install PyPDF2
```

### Transactions Not Created
- Check user exists in database
- Verify M-Pesa code format
- Check server logs for errors

### Date Parsing Issues
The parser supports multiple date formats. If your format isn't recognized, add it to the parser's format list in `transactions/utils/mpesa_parser.py`.

## API Documentation

### Success Response
```json
{
  "success": true,
  "created_transactions": 8,
  "skipped_duplicates": 2,
  "total_processed": 10,
  "errors": [],
  "file_type": "csv"
}
```

### Error Response
```json
{
  "detail": "No file uploaded"
}
```

### Permission
The upload endpoint has `AllowAny` permission for development. For production, implement proper authentication.
