"""
Payment provider interfaces and Razorpay cryptographic HMAC-SHA256 verification.
Enforces offline cryptographic validation (safe in test/ci without live API keys).
"""

from decimal import Decimal
import hashlib
import hmac
from typing import Any, Dict, Optional
from django.conf import settings


class BasePaymentProvider:
    def verify_payment_signature(self, **kwargs) -> bool:
        raise NotImplementedError

    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        raise NotImplementedError


class CODProvider(BasePaymentProvider):
    def verify_payment_signature(self, **kwargs) -> bool:
        return True

    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        return True


class RazorpayProvider(BasePaymentProvider):
    """
    Razorpay payment integration with HMAC-SHA256 signature verification.
    """

    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None, webhook_secret: Optional[str] = None):
        self.key_id = key_id or getattr(settings, "RAZORPAY_KEY_ID", "rzp_test_placeholder")
        self.key_secret = key_secret or getattr(settings, "RAZORPAY_KEY_SECRET", "placeholder_secret_key_12345")
        self.webhook_secret = webhook_secret or getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "placeholder_webhook_secret_67890")

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """
        Verifies checkout payment signature using HMAC SHA256 of 'order_id|payment_id' with key_secret.
        """
        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return False

        message = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
        computed = hmac.new(
            self.key_secret.encode("utf-8"),
            message,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(computed.lower(), razorpay_signature.strip().lower())

    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        """
        Verifies inbound webhook payload signature using HMAC SHA256 with webhook_secret.
        """
        if not raw_body or not signature:
            return False

        computed = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(computed.lower(), signature.strip().lower())

    @staticmethod
    def generate_test_payment_signature(order_id: str, payment_id: str, secret: str) -> str:
        """
        Utility for generating valid HMAC vectors in tests.
        """
        message = f"{order_id}|{payment_id}".encode("utf-8")
        return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

    @staticmethod
    def generate_test_webhook_signature(body: bytes, secret: str) -> str:
        """
        Utility for generating valid webhook signatures in tests.
        """
        return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
