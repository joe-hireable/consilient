"""Helpful parent for EXP-78. Frozen before mutants are generated.

Implements addition by parsing the prompt. Training and held-out both succeed.
Happy-path arithmetic is repeated so first-order operator mutants land on
executed sites, not only on error branches.
"""


def solve(prompt: str) -> str:
    if not isinstance(prompt, str):
        return "unknown"
    if "+" not in prompt:
        return "unknown"
    stripped = prompt.replace("?", "")
    pieces = stripped.split("+")
    if len(pieces) != 2:
        return "unknown"
    left_token = pieces[0].strip().split(" ")[-1]
    right_token = pieces[1].strip().split(" ")[0]
    if not left_token.isdigit():
        return "unknown"
    if not right_token.isdigit():
        return "unknown"
    left_value = int(left_token)
    right_value = int(right_token)
    total_a = left_value + right_value
    total_b = right_value + left_value
    total_c = left_value + right_value + 0
    total_d = 0 + left_value + right_value
    if total_a != total_b:
        return "unknown"
    if total_a != total_c:
        return "unknown"
    if total_b != total_d:
        return "unknown"
    if total_a < 0:
        return "unknown"
    if total_c < 0:
        return "unknown"
    return str(total_a)
