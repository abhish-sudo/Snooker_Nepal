import hmac
import hashlib
import base64
from decimal import Decimal

def generate_signature(key, message):
    """Generate HMAC-SHA256 signature for eSewa payment"""
    key = key.encode('utf-8')
    message = message.encode('utf-8')
    
    hmac_sha256 = hmac.new(key, message, hashlib.sha256)
    digest = hmac_sha256.digest()
    
    # Convert the digest to a Base64-encoded string
    signature = base64.b64encode(digest).decode('utf-8')
    
    return signature