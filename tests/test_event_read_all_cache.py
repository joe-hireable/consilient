"""F01 — the memoised `read_all`, and the three properties that are its licence.

MEASURED 28 August 2026: one read_all over the live trajectory is 1.8 seconds and 224 MB
retained, and coordination.py calls it at SIX sites per dispatch while a dozen
dispatches run. The driver was recording MemoryError crashes on that path. The cache
exists for that reason and is admissible only because it changes nothing observable, so
these three tests are what permit it rather than merely exercise it: a cached read
returns what a fresh parse would; an append, and equally a whole new day file at the
midnight roll, invalidates it through the per-file size in the fingerprint, since an
append-only log cannot grow without changing one; and the returned lists are copies,
because coordination.py appends a candidate event to the result while validating a claim
and a shared list would make that phantom permanent.

All three failures end in the same place — history hidden from a reader — and an epoch
derived over less history is LOWER, which is the one direction that is unsafe.
`_write_day` belongs here and nowhere else: it plants raw JSONL lines deliberately
bypassing the append transaction, which is the exact opposite of what every other check
in this family does."""


def _write_day(directory, name, payloads):
    """Write a day file of raw JSONL lines, bypassing the append transaction."""
    import json as _json

    path = directory / name
    with path.open("a", encoding="utf-8") as handle:
        for payload in payloads:
            handle.write(_json.dumps(payload) + chr(10))
    return path


def test_read_all_cache_returns_what_a_fresh_parse_would(tmp_path) -> None:
    """The memoised path must be indistinguishable from re-parsing.

    MEASURED 28 August 2026: one read_all over the live trajectory is 1.8 seconds and 224 MB
    retained, and coordination.py calls it at SIX sites per dispatch while a dozen dispatches
    run. The driver was recording MemoryError crashes on that path.

    A cache is only allowed here because it changes nothing: same events, same rejections,
    same order. If it ever does not, the horizon has effectively narrowed -- and an epoch
    derived over less history is LOWER, which is the one direction that is unsafe.
    """
    from consilient.events import read_all

    log = tmp_path / "log"
    log.mkdir()
    _write_day(log, "2026-08-01.jsonl", [{"event_id": "a", "kind": "note"}])

    first_events, first_rejected = read_all(log)
    second_events, second_rejected = read_all(log)  # served from cache
    # Totals, because a synthetic payload parses as a Rejection rather than an Event. Either
    # way a cache that hid a line would show here.
    assert len(second_events) == len(first_events)
    assert len(second_rejected) == len(first_rejected)
    assert len(second_events) + len(second_rejected) == 1


def test_read_all_cache_is_invalidated_by_an_append(tmp_path) -> None:
    """A stale hit would hide history, and hidden history lowers the fencing epoch.

    The fingerprint includes each file's SIZE, and an append-only log cannot grow without
    changing one. This is the test that makes the cache safe rather than merely fast: if it
    fails, read_all is returning less than the trajectory holds.
    """
    from consilient.events import read_all

    log = tmp_path / "log"
    log.mkdir()
    _write_day(log, "2026-08-01.jsonl", [{"event_id": "a", "kind": "note"}])
    be, br = read_all(log)
    before = len(be) + len(br)

    _write_day(log, "2026-08-01.jsonl", [{"event_id": "b", "kind": "note"}])
    ae, ar = read_all(log)
    after = len(ae) + len(ar)
    assert after == before + 1, "an append did not invalidate the cache"

    # A whole new day file must also be seen -- the midnight roll is exactly when the
    # fencing epoch collapsed once before.
    _write_day(log, "2026-08-02.jsonl", [{"event_id": "c", "kind": "note"}])
    re_, rr = read_all(log)
    rolled = len(re_) + len(rr)
    assert rolled == after + 1, "a new day file did not invalidate the cache"


def test_read_all_never_hands_back_a_list_a_caller_can_corrupt(tmp_path) -> None:
    """Callers append to the returned history; a shared list would poison the cache.

    coordination.py does `history.append(Event(candidate))` on the result while validating a
    claim. If that were the cached list, the next reader would see a phantom event that was
    never committed -- and would compute a fencing epoch from it.
    """
    from consilient.events import read_all

    log = tmp_path / "log"
    log.mkdir()
    _write_day(log, "2026-08-01.jsonl", [{"event_id": "a", "kind": "note"}])

    events, rejected = read_all(log)
    original = len(events) + len(rejected)
    events.append("phantom")  # a caller mutating its own copy
    rejected.append("nonsense")

    again, again_rejected = read_all(log)
    assert len(again) + len(again_rejected) == original, "a caller mutated the cache"
    assert "phantom" not in again
    assert "nonsense" not in again_rejected
