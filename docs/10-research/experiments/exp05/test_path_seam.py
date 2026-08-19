"""The namespace and result-parsing seams in adapter #3 get checks (I2)."""

from adapter_cursor import to_wsl_path, usage_fields

CASES = [
    (
        r"C:\Users\jpbpr\Repositories\consilience",
        "/mnt/c/Users/jpbpr/Repositories/consilience",
    ),
    (r"D:\tmp\exp05_abc", "/mnt/d/tmp/exp05_abc"),
    ("/already/posix", "/already/posix"),
    (r"C:\a b\c", "/mnt/c/a b/c"),
]

if __name__ == "__main__":
    for inp, want in CASES:
        got = to_wsl_path(inp)
        assert got == want, f"{inp} -> {got}, wanted {want}"
        print(f"  ok  {inp}  ->  {got}")
    print(f"path seam: {len(CASES)}/{len(CASES)} pass")

    got = usage_fields(
        {
            "usage": {
                "inputTokens": 74781,
                "outputTokens": 918,
                "cacheReadTokens": 92160,
                "cacheWriteTokens": 0,
            }
        }
    )
    assert got == {
        "tokens_in": 74781,
        "tokens_out": 918,
        "cache_read_tokens": 92160,
        "cache_write_tokens": 0,
    }
    assert all(value is None for value in usage_fields({}).values())
    print("usage seam: live-shaped + missing-usage cases pass")
