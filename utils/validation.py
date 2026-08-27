from html import escape


def require_json(data, fields):
    if not isinstance(data, dict):
        return "Request body must be a JSON object."
    for field in fields:
        if field not in data or data[field] in (None, ""):
            return f"Missing required field: {field}."
    return None


def clean_text(value: str, max_len: int = 8000) -> str:
    value = (value or "").strip()
    if len(value) > max_len:
        raise ValueError(f"Text exceeds {max_len} characters.")
    return value


def safe_title(value: str) -> str:
    return escape((value or "Untitled").strip()[:120])
