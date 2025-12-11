import re
from datetime import datetime
from decimal import Decimal


class MPesaParser:
    """Parser for M-Pesa transaction statements in various formats"""
    
    @staticmethod
    def parse_sms(text):
        """
        Parse M-Pesa SMS notifications.
        Supports multiple SMS formats (received, sent, withdrawal, etc.)
        """
        if not text:
            return None

        # Pattern for received money
        received_pattern = re.compile(
            r'(?P<code>[A-Z0-9]{8,10})\s+Confirmed\.?'
            r'.*?received\s+(?:Ksh\s*)?(?P<amount>[0-9,]+\.?\d{0,2})'
            r'.*?from\s+(?P<sender>.*?)'
            r'(?:\s+on\s+(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\s+at\s+(?P<time>\d{1,2}:\d{2}\s*(?:AM|PM)?)|$)',
            re.IGNORECASE | re.DOTALL
        )
        
        # Pattern for sent money
        sent_pattern = re.compile(
            r'(?P<code>[A-Z0-9]{8,10})\s+Confirmed\.?'
            r'.*?(?:sent|paid)\s+(?:Ksh\s*)?(?P<amount>[0-9,]+\.?\d{0,2})'
            r'.*?to\s+(?P<recipient>.*?)'
            r'(?:\s+on\s+(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\s+at\s+(?P<time>\d{1,2}:\d{2}\s*(?:AM|PM)?)|$)',
            re.IGNORECASE | re.DOTALL
        )
        
        # Pattern for withdrawal
        withdrawal_pattern = re.compile(
            r'(?P<code>[A-Z0-9]{8,10})\s+Confirmed\.?'
            r'.*?(?:withdrew|withdraw)\s+(?:Ksh\s*)?(?P<amount>[0-9,]+\.?\d{0,2})'
            r'.*?from\s+(?P<agent>.*?)'
            r'(?:\s+on\s+(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\s+at\s+(?P<time>\d{1,2}:\d{2}\s*(?:AM|PM)?)|$)',
            re.IGNORECASE | re.DOTALL
        )

        # Try each pattern
        for pattern, trans_type in [
            (received_pattern, "C2B"),
            (sent_pattern, "B2C"),
            (withdrawal_pattern, "B2C")
        ]:
            match = pattern.search(text)
            if match:
                data = match.groupdict()
                amount = float(data["amount"].replace(",", ""))
                
                # Parse date if available
                date_obj = datetime.now()
                if data.get("date") and data.get("time"):
                    try:
                        date_str = f"{data['date']} {data['time']}"
                        for fmt in ["%m/%d/%y %I:%M %p", "%d/%m/%Y %H:%M", "%m/%d/%Y %I:%M %p"]:
                            try:
                                date_obj = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                    except:
                        pass
                
                # Extract phone number
                phone = ""
                contact = data.get("sender") or data.get("recipient") or data.get("agent") or ""
                phone_match = re.search(r'(254\d{9}|\d{10})', contact)
                if phone_match:
                    phone = phone_match.group(1)
                
                return {
                    "mpesa_code": data["code"],
                    "amount": amount,
                    "phone_number": phone,
                    "date": date_obj,
                    "trans_type": trans_type,
                    "description": text.strip()[:200]
                }
        
        return None
    
    @staticmethod
    def parse_csv_row(row):
        """
        Parse a row from M-Pesa CSV statement.
        Handles various CSV formats from M-Pesa statements.
        """
        try:
            # Common M-Pesa CSV columns
            mpesa_code = row.get("Receipt No") or row.get("Receipt No.") or row.get("Transaction ID") or row.get("mpesa_code")
            
            # Parse amount
            amount_str = (
                row.get("Paid In") or row.get("Withdrawn") or 
                row.get("Amount") or row.get("amount") or "0"
            )
            amount = float(str(amount_str).replace(",", "").replace("Ksh", "").strip())
            
            # Determine transaction type
            trans_type = "C2B"
            if row.get("Withdrawn") or row.get("Paid Out"):
                trans_type = "B2C"
            elif row.get("trans_type"):
                trans_type = row.get("trans_type")
            
            # Parse date
            date_str = row.get("Completion Time") or row.get("Date") or row.get("date")
            date_obj = datetime.now()
            if date_str:
                for fmt in [
                    "%d/%m/%Y %H:%M:%S",
                    "%m/%d/%Y %I:%M:%S %p",
                    "%Y-%m-%d %H:%M:%S",
                    "%d-%m-%Y %H:%M",
                    "%Y-%m-%d"
                ]:
                    try:
                        date_obj = datetime.strptime(str(date_str).strip(), fmt)
                        break
                    except ValueError:
                        continue
            
            # Extract phone number
            phone = (
                row.get("Other Party Info") or 
                row.get("Phone Number") or 
                row.get("phone_number") or ""
            )
            
            # Extract description
            description = (
                row.get("Details") or 
                row.get("Description") or 
                row.get("description") or ""
            )
            
            return {
                "mpesa_code": str(mpesa_code).strip(),
                "amount": amount,
                "phone_number": str(phone).strip(),
                "date": date_obj,
                "trans_type": trans_type,
                "description": str(description)[:200]
            }
        except Exception as e:
            print(f"Error parsing CSV row: {e}")
            return None
    
    @staticmethod
    def parse_pdf_text(text):
        """
        Extract M-Pesa transactions from PDF text content.
        Returns a list of transaction dictionaries.
        """
        transactions = []
        
        # Split text into lines
        lines = text.split('\n')
        
        # Pattern to match transaction lines in M-Pesa statements
        # Format: Receipt No | Date | Details | Paid In | Withdrawn | Balance
        transaction_pattern = re.compile(
            r'(?P<code>[A-Z0-9]{8,10})\s+'
            r'(?P<date>\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM))?)\s+'
            r'(?P<details>.*?)\s+'
            r'(?:(?P<paid_in>[0-9,]+\.?\d{0,2})\s+)?'
            r'(?:(?P<withdrawn>[0-9,]+\.?\d{0,2})\s+)?'
            r'(?P<balance>[0-9,]+\.?\d{0,2})',
            re.IGNORECASE
        )
        
        for line in lines:
            match = transaction_pattern.search(line)
            if match:
                data = match.groupdict()
                
                # Determine amount and type
                amount = 0
                trans_type = "C2B"
                
                if data.get("paid_in"):
                    amount = float(data["paid_in"].replace(",", ""))
                    trans_type = "C2B"
                elif data.get("withdrawn"):
                    amount = float(data["withdrawn"].replace(",", ""))
                    trans_type = "B2C"
                
                if amount == 0:
                    continue
                
                # Parse date
                date_obj = datetime.now()
                try:
                    date_str = data["date"].strip()
                    for fmt in [
                        "%d/%m/%Y %H:%M:%S",
                        "%m/%d/%Y %I:%M:%S %p",
                        "%d/%m/%Y %H:%M",
                        "%m/%d/%Y %I:%M %p"
                    ]:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                except:
                    pass
                
                # Extract phone from details
                details = data["details"]
                phone = ""
                phone_match = re.search(r'(254\d{9}|\d{10})', details)
                if phone_match:
                    phone = phone_match.group(1)
                
                transactions.append({
                    "mpesa_code": data["code"],
                    "amount": amount,
                    "phone_number": phone,
                    "date": date_obj,
                    "trans_type": trans_type,
                    "description": details.strip()[:200]
                })
        
        return transactions


# Legacy function for backward compatibility
def parse_mpesa_sms(text):
    """Legacy function - use MPesaParser.parse_sms instead"""
    return MPesaParser.parse_sms(text)
