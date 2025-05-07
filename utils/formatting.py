# utils/formatting.py

def format_in_indian_style(value):
    """
    Format a number in Indian style: e.g., 1,00,000 instead of 100,000.
    Works for KPIs and Plotly chart labels.
    """
    try:
        value = int(value)
        s = str(value)
        if len(s) > 3:
            last_three = s[-3:]
            rest = s[:-3]
            parts = []
            while len(rest) > 2:
                parts.append(rest[-2:])
                rest = rest[:-2]
            if rest:
                parts.append(rest)
            parts.reverse()
            formatted = ",".join(parts) + "," + last_three
            return formatted
        else:
            return s
    except Exception:
        return value