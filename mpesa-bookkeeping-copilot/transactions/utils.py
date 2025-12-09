import re
from dateutil import parser

# Very simple pattern example — tweak for M-Pesa SMS formats
MPESA_SMS_REGEX = r"(?P<amount>\d+(?:,\d{3})*(?:\.\d+)?)\s*Ksh.*?(?P<mpesa_code>[A-Z0-9]{6,})"

def parse_mpesa_sms(text):
    # normalize commas e.g. 2,500 -> 2500
    match = re.search(MPESA_SMS_REGEX, text.replace(",", ""))
    if not match:
        return None
    amount = float(match.group("amount"))
    mpesa_code = match.group("mpesa_code")
    # In a real parser, parse date/time and phone numbers too
    return {"amount": amount, "mpesa_code": mpesa_code}
