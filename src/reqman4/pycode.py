import re
from typing import Any

def is_python(name:str, value:Any) -> str|None:
    if isinstance(value, str) and value.strip().startswith(("def ","lambda ")):
        signature = value.strip().splitlines()[0]
        # check if it's a valid python function definition
        if signature.startswith("def ") and signature.endswith(":"):
            # extract function name
            match = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', signature)
            if match:
                func_name = match.group(1)
                if func_name == name:
                    return value
        elif signature.startswith("lambda "):
            # it's a lambda, but the key must be the same
            return f"{name} = {value}"
    return None
