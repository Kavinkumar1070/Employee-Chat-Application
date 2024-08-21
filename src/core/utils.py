


def normalize_string(value: str) -> str:
    """Trims whitespace from the start and end of the string and converts it to lowercase."""
    if isinstance(value, str):
        return value.strip().lower()
    return value