"""The one piece of genuinely new logic in adapter #3 gets a check (I2)."""

from adapter_cursor import to_wsl_path

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
