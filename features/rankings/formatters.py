def format_value(value: int, format_type: str) -> str:
    """Convert a raw stat value to a display string."""
    value = int(value)
    if format_type == "hours":
        hours = value // 20 // 3600
        return f"{hours:,}h"
    elif format_type == "currency":
        return f"₡ {value:,}"
    elif format_type == "km":  # value stored in centimeters
        km = value / 100_000
        return f"{km:,.1f} km"
    else:  # number
        return f"{value:,}"
