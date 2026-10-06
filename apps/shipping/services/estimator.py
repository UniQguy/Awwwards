"""
Delivery estimate engine resolving serviceability and transit days from PIN codes.
"""

from dataclasses import dataclass
import datetime
import re
from zoneinfo import ZoneInfo

from ..models import PincodeServiceability, ShippingZone

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
PIN_REGEX = re.compile(r"^[1-9][0-9]{5}$")


@dataclass(frozen=True)
class DeliveryEstimate:
    serviceable: bool
    date_min: datetime.date | None = None
    date_max: datetime.date | None = None
    est_days_min: int = 0
    est_days_max: int = 0
    cod_allowed: bool = False
    is_sample: bool = True
    matched_by: str = "none"  # "exact", "zone_prefix", or "none"
    unavailable_reason: str | None = None


def estimate(pincode: str, today: datetime.date | None = None) -> DeliveryEstimate:
    """
    Compute estimated delivery window for a 6-digit Indian PIN code.
    Precedence:
        1. Exact PincodeServiceability match.
        2. Longest active ShippingZone prefix (3-digit, then 2-digit, then 1-digit).
        3. Returns unserviceable (never returns placeholder dates for unserviceable destinations).
    """
    if today is None:
        today = datetime.datetime.now(KOLKATA_TZ).date()

    clean_pin = str(pincode).strip()
    if not PIN_REGEX.match(clean_pin):
        return DeliveryEstimate(
            serviceable=False,
            unavailable_reason="Invalid PIN code format. Must be a 6-digit Indian postal code.",
        )

    # 1. Look up exact PincodeServiceability override
    exact = PincodeServiceability.objects.filter(pincode=clean_pin).first()
    if exact is not None:
        if not exact.is_serviceable:
            return DeliveryEstimate(
                serviceable=False,
                matched_by="exact",
                unavailable_reason="Delivery to this PIN code is currently suspended.",
            )
        return DeliveryEstimate(
            serviceable=True,
            date_min=today + datetime.timedelta(days=exact.est_days_min),
            date_max=today + datetime.timedelta(days=exact.est_days_max),
            est_days_min=exact.est_days_min,
            est_days_max=exact.est_days_max,
            cod_allowed=exact.cod_allowed,
            is_sample=(exact.source == "sample"),
            matched_by="exact",
        )

    # 2. Longest prefix lookup in active ShippingZones (3, 2, 1)
    for prefix_len in (3, 2, 1):
        prefix = clean_pin[:prefix_len]
        zone = (
            ShippingZone.objects.filter(pin_prefix=prefix, is_active=True)
            .order_by("-pin_prefix")
            .first()
        )
        if zone is not None:
            return DeliveryEstimate(
                serviceable=True,
                date_min=today + datetime.timedelta(days=zone.est_days_min),
                date_max=today + datetime.timedelta(days=zone.est_days_max),
                est_days_min=zone.est_days_min,
                est_days_max=zone.est_days_max,
                cod_allowed=zone.cod_allowed,
                is_sample=(zone.source == "sample"),
                matched_by="zone_prefix",
            )

    # 3. Unserviceable fallback
    return DeliveryEstimate(
        serviceable=False,
        unavailable_reason="Delivery unavailable for this PIN code.",
    )


estimate_delivery = estimate

