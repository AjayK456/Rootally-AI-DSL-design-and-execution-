import re
import json

def parse_number_token(s):
    s = s.strip().lower()
    # common words
    s = s.replace("1 million", "1000000").replace("1m", "1000000")
    s = s.replace(",", "")
    # percent like "30 percent" handled elsewhere
    try:
        if s.endswith("%"):
            return {"type":"percent_literal", "value": float(s[:-1])}
        if '.' in s:
            return {"type":"number", "value": float(s)}
        return {"type":"number", "value": int(s)}
    except:
        return None

def make_field(name):
    return {"type":"field", "name": name.lower()}

def make_indicator(name, arg_field, n):
    return {"type":"indicator", "name": name.lower(), "args": [ {"type":"field", "name": arg_field.lower()}, int(n) ]}

def make_yesterday_field(name):
    return {"type":"yesterday_field", "name": name.lower()}

def make_binary_expr(op, left, right):
    # left/right can be either raw numbers or structured nodes
    return {"type":"binary_expr", "op":op, "left": left, "right": right}

def number_from_phrase(phrase):
    phrase = phrase.lower().strip()
    phrase = phrase.replace("1 million", "1000000").replace("1m", "1000000")
    m = re.search(r'([\d,.]+)', phrase)
    if m:
        tok = m.group(1).replace(",", "")
        if '.' in tok:
            return {"type":"number","value": float(tok)}
        else:
            return {"type":"number","value": int(tok)}
    return None

def nl_to_json(nl_text):
    """
    Very small rule-based mapper that handles the example patterns and similar phrasings.
    Returns: dict with 'entry' and 'exit' lists of condition objects (see schema).
    """
    text = nl_text.strip()
    low = text.lower()

    out = {"entry": [], "exit": []}

    # helper to split AND (simple)
    parts = re.split(r'\s+and\s+', text, flags=re.IGNORECASE)

    # Determine whether rule is ENTRY or EXIT by keywords
    is_exit = bool(re.search(r'\b(exit|sell|close)\b', low))
    is_entry = bool(re.search(r'\b(buy|enter|trigger entry|enter when|trigger)\b', low)) or (not is_exit)

    # Process each clause separately
    conditions = []
    for clause in parts:
        c = clause.strip()

        # 1) "close price is above the 20-day moving average"
        m = re.search(r'(?:the\s+)?(?P<left>close|price|open|high|low|volume)\s+(?:price\s+)?(?:is\s+)?(?P<op>above|over|>|greater than|below|under|<|<=|>=|==)\s+(?P<right>[\w\s\-\(\),%\.]+)', c, flags=re.IGNORECASE)
        if m:
            left = m.group('left').lower()
            op_raw = m.group('op').lower()
            right_phrase = m.group('right').strip()

            # normalize op
            if op_raw in ("above","over","greater than",">"):
                op = ">"
            elif op_raw in ("below","under","<"):
                op = "<"
            elif op_raw == ">=":
                op = ">="
            elif op_raw == "<=":
                op = "<="
            elif op_raw == "==":
                op = "=="
            else:
                op = ">"

            # check for moving average pattern: "20-day moving average" or "sma(close,20)"
            ma = re.search(r'(\d+)[\s-]*day\s+moving\s+average', right_phrase, flags=re.IGNORECASE)
            sma_call = re.search(r'sma\(\s*(?P<fld>\w+)\s*,\s*(?P<n>\d+)\s*\)', right_phrase, flags=re.IGNORECASE)
            rsi_call = re.search(r'rsi\(\s*(?P<fld>\w+)\s*,\s*(?P<n>\d+)\s*\)', right_phrase, flags=re.IGNORECASE)
            if sma_call:
                fld = sma_call.group('fld')
                n = sma_call.group('n')
                right = make_indicator('sma', fld, n)
            elif ma:
                n = int(ma.group(1))
                right = make_indicator('sma', left, n)  # assume SMA of the same field unless specified
            elif rsi_call:
                fld = rsi_call.group('fld')
                n = rsi_call.group('n')
                right = make_indicator('rsi', fld, n)
            else:
                # try numeric
                num = number_from_phrase(right_phrase)
                if num:
                    right = num
                else:
                    # fallback: treat as field or indicator text
                    if 'sma' in right_phrase.lower():
                        m2 = re.search(r'sma\(\s*(\w+)\s*,\s*(\d+)\s*\)', right_phrase, flags=re.IGNORECASE)
                        if m2:
                            right = make_indicator('sma', m2.group(1), m2.group(2))
                        else:
                            right = {"type":"raw","text": right_phrase}
                    else:
                        right = {"type":"raw","text": right_phrase}

            cond = {
                "type":"compare",
                "left": make_field(left if left != 'price' else 'close'),
                "op": op,
                "right": right
            }
            conditions.append(cond)
            continue

        # 2) "price crosses above yesterday's high" OR "enter when close crosses above the SMA(close,50)"
        m2 = re.search(r'(?P<left>close|price|open|high|low|volume|\w+\([^)]+\))\s+cross(?:es)?\s*(?:_| )?(?P<dir>above|below)\s+(?P<right>[\w\(\)\'s_ -]+)', c, flags=re.IGNORECASE)
        if m2:
            left_raw = m2.group('left').strip()
            dir_ = m2.group('dir').lower()
            right_raw = m2.group('right').strip()

            def parse_operand(tok):
                tok = tok.strip()
                # sma or rsi call?
                sma_call = re.search(r'sma\(\s*(?P<fld>\w+)\s*,\s*(?P<n>\d+)\s*\)', tok, flags=re.IGNORECASE)
                rsi_call = re.search(r'rsi\(\s*(?P<fld>\w+)\s*,\s*(?P<n>\d+)\s*\)', tok, flags=re.IGNORECASE)
                if tok.lower() in ('price','close','open','high','low','volume'):
                    return make_field(tok if tok.lower()!='price' else 'close')
                if 'yesterday' in tok.lower():
                    # e.g., "yesterday's high" or "yesterday high"
                    fldm = re.search(r'yesterday[\'s\s]*\s*(?P<f>\w+)', tok, flags=re.IGNORECASE)
                    if fldm:
                        return make_yesterday_field(fldm.group('f'))
                    else:
                        # fallback
                        return {"type":"yesterday_field","name":"close"}
                if sma_call:
                    return make_indicator('sma', sma_call.group('fld'), sma_call.group('n'))
                if rsi_call:
                    return make_indicator('rsi', rsi_call.group('fld'), rsi_call.group('n'))
                # otherwise raw
                return {"type":"raw","text": tok}

            left_op = parse_operand(left_raw)
            right_op = parse_operand(right_raw)
            cond = {"type":"cross", "dir": dir_, "left": left_op, "right": right_op}
            conditions.append(cond)
            continue

        # 3) "Exit when RSI(14) is below 30."
        m3 = re.search(r'rsi\(\s*(?P<fld>\w+)\s*,\s*(?P<n>\d+)\s*\)\s*(?:is\s+)?(?P<op><|>|<=|>=|==|below|above)\s*(?P<val>[\d\.]+)', c, flags=re.IGNORECASE)
        if m3:
            fld = m3.group('fld'); n = m3.group('n'); op_raw = m3.group('op'); val = m3.group('val')
            if op_raw in ('below','<'):
                op = '<'
            elif op_raw in ('above','>'):
                op = '>'
            else:
                op = op_raw
            right = {"type":"number", "value": float(val) if '.' in val else int(val)}
            left = make_indicator('rsi', fld, n)
            cond = {"type":"compare","left": left, "op": op, "right": right}
            conditions.append(cond)
            continue

        # 4) "Trigger entry when volume increases by more than 30 percent compared to last week."
        m4 = re.search(r'volume .*?increases by more than\s*(?P<pct>\d+)\s*%.*last week', c, flags=re.IGNORECASE)
        if m4:
            pct = float(m4.group('pct'))
            factor = 1 + pct/100.0
            # map "last week" to sma(volume,5)
            rhs = make_indicator('sma', 'volume', 5)
            right_expr = make_binary_expr('*', factor, rhs)
            cond = {"type":"compare", "left": make_field('volume'), "op": ">", "right": right_expr}
            conditions.append(cond)
            continue

        # 5) fallback: try to parse direct patterns like "rsi(close,14) < 30"
        m5 = re.search(r'(?P<left_expr>[\w\(\),]+)\s*(?P<op>>|<|>=|<=|==)\s*(?P<right_expr>[\w\(\),.%]+)', c)
        if m5:
            left_expr = m5.group('left_expr')
            op = m5.group('op')
            right_expr = m5.group('right_expr')
            # parse left_expr if it's a function like rsi(...) or sma(...)
            if left_expr.lower().startswith('rsi'):
                mm = re.search(r'rsi\(\s*(?P<fld>\w+)\s*,\s*(?P<n>\d+)\s*\)', left_expr, flags=re.IGNORECASE)
                left = make_indicator('rsi', mm.group('fld'), mm.group('n')) if mm else {"type":"raw","text":left_expr}
            elif left_expr.lower().startswith('sma'):
                mm = re.search(r'sma\(\s*(?P<fld>\w+)\s*,\s*(?P<n>\d+)\s*\)', left_expr, flags=re.IGNORECASE)
                left = make_indicator('sma', mm.group('fld'), mm.group('n')) if mm else {"type":"raw","text":left_expr}
            else:
                left = make_field(left_expr)

            # right
            num = number_from_phrase(right_expr)
            if num:
                right = num
            else:
                # indicator?
                mm2 = re.search(r'sma\(\s*(?P<fld>\w+)\s*,\s*(?P<n>\d+)\s*\)', right_expr, flags=re.IGNORECASE)
                if mm2:
                    right = make_indicator('sma', mm2.group('fld'), mm2.group('n'))
                else:
                    right = {"type":"raw","text": right_expr}

            cond = {"type":"compare","left": left, "op": op, "right": right}
            conditions.append(cond)
            continue

        # If nothing matched, append raw clause for manual inspection
        conditions.append({"type":"raw_clause","text": c})

    # place conditions into entry or exit
    if is_exit and not is_entry:
        out['exit'].extend(conditions)
    elif is_entry and not is_exit:
        out['entry'].extend(conditions)
    else:
        # If both or ambiguous, try keyword presence: if clause has 'exit' put into exit else entry
        # But by default: map to entry if "buy/enter/trigger" appears, else exit if exit word present
        if is_entry:
            out['entry'].extend(conditions)
        else:
            out['exit'].extend(conditions)

    return out

# pretty-print helper
def pretty(nl):
    j = nl_to_json(nl)
    print(json.dumps(j, indent=2))
if __name__ == "__main__":
    import json

    # Test sentence (you can change it anytime)
    nl_sentence = "Buy when price > SMA(close, 20) and volume > 1,000,000"

    # Call the function
    result = nl_to_json(nl_sentence)

    # Print output nicely
    print(json.dumps(result, indent=2))
