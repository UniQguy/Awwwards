"""
Official Indian States and Union Territories with 2-digit GST State Codes.
Table Status: Canonical list; verify against the official GST state code list.
"""

from .exceptions import InvalidStateError

# Official 2-digit GST State Code mapping (36 States & Union Territories)
# Source: GST Council / CBIC State Code Directory
GST_STATE_CODES: dict[str, str] = {
    "Jammu and Kashmir": "01",
    "Himachal Pradesh": "02",
    "Punjab": "03",
    "Chandigarh": "04",
    "Uttarakhand": "05",
    "Haryana": "06",
    "Delhi": "07",
    "Rajasthan": "08",
    "Uttar Pradesh": "09",
    "Bihar": "10",
    "Sikkim": "11",
    "Arunachal Pradesh": "12",
    "Nagaland": "13",
    "Manipur": "14",
    "Mizoram": "15",
    "Tripura": "16",
    "Meghalaya": "17",
    "Assam": "18",
    "West Bengal": "19",
    "Jharkhand": "20",
    "Odisha": "21",
    "Chhattisgarh": "22",
    "Madhya Pradesh": "23",
    "Gujarat": "24",
    "Dadra and Nagar Haveli and Daman and Diu": "26",
    "Maharashtra": "27",
    "Karnataka": "29",
    "Goa": "30",
    "Lakshadweep": "31",
    "Kerala": "32",
    "Tamil Nadu": "33",
    "Puducherry": "34",
    "Andaman and Nicobar Islands": "35",
    "Telangana": "36",
    "Andhra Pradesh": "37",
    "Ladakh": "38",
}

# Fast case-insensitive lookup table
_LOOKUP: dict[str, str] = {name.lower(): name for name in GST_STATE_CODES}


def normalize_state_name(raw_name: str | None) -> str:
    """
    Normalize an Indian State or Union Territory name to canonical casing.
    Strips whitespace and performs case-insensitive matching.
    Raises:
        InvalidStateError if the state name is not in the official 36 state roster.
    """
    if not raw_name or not isinstance(raw_name, str):
        raise InvalidStateError(f"Invalid state: '{raw_name}' is empty or invalid.")

    cleaned = raw_name.strip().lower()
    if cleaned in _LOOKUP:
        return _LOOKUP[cleaned]

    raise InvalidStateError(
        f"'{raw_name}' is not a recognized Indian State or Union Territory."
    )


def get_gst_code(state_name: str) -> str:
    """Get the 2-digit GST state code for a state name."""
    canonical = normalize_state_name(state_name)
    return GST_STATE_CODES[canonical]
