
def mask_value(value, sensitivity: str):
    if value is None:
        return None

    if sensitivity == "P":
        return value

    if sensitivity == "I":
        return value

    if sensitivity == "S":
        return str(value)[:2] + "****"

    if sensitivity == "H":
        return "********"

    return value