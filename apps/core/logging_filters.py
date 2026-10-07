"""
Logging filters for security hardening.
Redacts guest order tokens, email addresses, and payment gateway credentials from all log outputs.
"""

import logging
import re


class SensitiveDataFilter(logging.Filter):
    """
    Log record filter that redacts sensitive customer and payment tokens:
    - Guest access tokens in query params: ?token=xyz -> ?token=[REDACTED]
    - Signature tokens: ?sig=xyz -> ?sig=[REDACTED]
    - Email addresses: john.doe@example.com -> j***e@example.com
    - Razorpay identifiers/secrets: rzp_test_abcdef1234 -> rzp_test_abcd[REDACTED]
    """

    TOKEN_REGEX = re.compile(r"([?&]token=)[a-zA-Z0-9_\-\.]+", re.IGNORECASE)
    SIG_REGEX = re.compile(r"([?&]sig=)[a-zA-Z0-9_\-\.]+", re.IGNORECASE)
    EMAIL_REGEX = re.compile(r"\b([A-Za-z0-9._%+-]{1,2})[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
    RAZORPAY_REGEX = re.compile(r"\b(rzp_(?:test|live)_[a-zA-Z0-9]{4})[a-zA-Z0-9]+\b")

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self.redact(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(
                    self.redact(v) if isinstance(v, str) else v
                    for v in record.args
                )
        return True

    @classmethod
    def redact(cls, text: str) -> str:
        if not isinstance(text, str):
            return text
        text = cls.TOKEN_REGEX.sub(r"\1[REDACTED]", text)
        text = cls.SIG_REGEX.sub(r"\1[REDACTED]", text)
        text = cls.EMAIL_REGEX.sub(r"\1***@\2", text)
        text = cls.RAZORPAY_REGEX.sub(r"\1[REDACTED]", text)
        return text
