import re

def _num_from_text(s: str):
    s = s.lower().replace(",", "").strip()
    if s.endswith("m"):
        return str(float(s[:-1]) * 1_000_000)
    if s.endswith("k"):
        return str(float(s[:-1]) * 1000)
    return s


def nlp_to_dsl(nl: str):
    if not nl:
        raise ValueError("Empty input")

    text = nl.lower().strip()

    # ------------------------------
    # PRICE → close
    # ------------------------------
    text = text.replace("price", "close")

    # ------------------------------
    # SMA patterns
    # ------------------------------
    text = re.sub(r"(\d+)[ -]?day moving average", r"sma(close,\1)", text)
    text = re.sub(r"(\d+)[ -]?day sma", r"sma(close,\1)", text)
    text = re.sub(r"sma\s*\(?\s*(\d+)\s*\)?", r"sma(close,\1)", text)

    # ------------------------------
    # RSI
    # ------------------------------
    text = re.sub(r"rsi\(?\s*(\d{1,2})\)?", r"rsi(close,\1)", text)

    # ------------------------------
    # Comparisons
    # ------------------------------
    text = text.replace("is above", ">")
    text = text.replace("closes above", ">")
    text = text.replace("above", ">")

    text = text.replace("is below", "<")
    text = text.replace("falls below", "<")
    text = text.replace("drops below", "<")
    text = text.replace("below", "<")

    # ------------------------------
    # Volume normalization
    # ------------------------------
    text = re.sub(r"(\d+(?:\.\d+)?k)\b", lambda m: _num_from_text(m.group(1)), text)
    text = re.sub(r"(\d+(?:\.\d+)?m)\b", lambda m: _num_from_text(m.group(1)), text)
    text = re.sub(r"(\d+(?:\.\d+)?)(?:\s*million)\b",
                  lambda m: str(float(m.group(1)) * 1_000_000), text)

    # ------------------------------
    # Split entry/exit
    # ------------------------------
    entry = ""
    exit_ = ""
    parts = re.split(r"[.\n]", text)

    for p in parts:
        p = p.strip()
        if not p:
            continue

        if p.startswith(("buy", "enter", "open", "long")):
            entry = re.sub(r"^(buy|enter|open|long)\s*(when)?\s*", "", p)
        elif p.startswith(("exit", "sell", "close", "stop", "short")):
            exit_ = re.sub(r"^(exit|sell|close|stop|short)\s*(when)?\s*", "", p)
        else:
            if not entry:
                entry = p
            elif not exit_:
                exit_ = p

    # ------------------------------
    # Cleanup function
    # ------------------------------
    def clean(x):
        x = re.sub(r"\b(the|a|an|when|then|is|and also)\b", " ", x)
        x = re.sub(r"\s+", " ", x)
        return x.strip()

    entry = clean(entry)
    exit_ = clean(exit_)

    # ------------------------------
    # Convert AND explicitly
    # ------------------------------
    entry = entry.replace(" and ", " AND ")
    exit_ = exit_.replace(" and ", " AND ")

    # ------------------------------
    # Final DSL
    # ------------------------------
    lines = []
    if entry:
        lines.append("ENTRY:")
        lines.append(entry)

    if exit_:
        lines.append("")
        lines.append("EXIT:")
        lines.append(exit_)

    return "\n".join(lines).strip()
