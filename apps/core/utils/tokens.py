"""
Guest order access token generation and cryptographic verification.
"""

import datetime
import hashlib
import hmac
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

GUEST_TOKEN_SALT = "electrocart.guest.order.access"


def make_guest_token(order_number: str) -> tuple[str, str]:
    """
    Generate a signed guest access token and its SHA-256 storage hash.
    Returns:
        tuple of (raw_token, sha256_hash)
    The raw token is returned once to the guest; the hash is persisted in the database.
    """
    signer = TimestampSigner(salt=GUEST_TOKEN_SALT)
    raw_token = signer.sign(order_number)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return raw_token, token_hash


def verify_guest_token(
    raw_token: str, order_number: str, stored_hash: str, max_age_days: int = 30
) -> bool:
    """
    Cryptographically verify that a guest token is valid, matches the order,
    matches the persisted hash, and has not expired.
    Uses constant-time comparison to prevent timing side-channel attacks.
    """
    if not raw_token or not order_number or not stored_hash:
        return False

    computed_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(computed_hash, stored_hash):
        return False

    signer = TimestampSigner(salt=GUEST_TOKEN_SALT)
    try:
        unsigned_value = signer.unsign(
            raw_token, max_age=datetime.timedelta(days=max_age_days)
        )
    except (BadSignature, SignatureExpired):
        return False

    return hmac.compare_digest(unsigned_value, order_number)
