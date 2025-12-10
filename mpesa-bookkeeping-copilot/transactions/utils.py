import re
from datetime import datetime

def parse_mpesa_sms(text):
    if not text:
        return None

    data = {}

    # 1. Extract M-PESA code
    # Matches formats like QFG45D123, RL82GH90T, etc.
    code_match = re.search(r"\b([A-Z]{2,3}\d[A-Z0-9]{5,9})\b", text)
    if code_match:
        data["mpesa_code"] = code_match.group(1)
    else:
        return None  # very important

    # 2. Extract amount received or sent
    amt_match = re.search(r"Ksh\s?([\d,]+\.\d{2})", text)
    if amt_match:
        data["amount"] = float(amt_match.group(1).replace(",", ""))

    # 3. Extract phone number
    phone_match = re.search(r"from\s+(\d{10,12})", text)
    if phone_match:
        data["phone_number"] = phone_match.group(1)

    # 4. Extract date and time
    date_match = re.search(r"on\s+(\d{1,2}/\d{1,2}/\d{2})\s+at\s+([\d:]+\s?[APM]{2})", text)
    if date_match:
        raw_date, raw_time = date_match.groups()
        try:
            data["date"] = datetime.strptime(f"{raw_date} {raw_time}", "%m/%d/%y %I:%M %p")
        except:
            pass

    # 5. Determine transaction type
    if "received" in text.lower():
        data["trans_type"] = "C2B"
    elif "sent" in text.lower():
        data["trans_type"] = "P2P"
    else:
        data["trans_type"] = "C2B"

    return data
