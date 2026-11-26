# Assignment: Sliding window counter

## Problem

Count events per key inside a sliding time window. Each call records one event for a key at a given
time and returns how many events that key has inside the window ending at that time. Time is passed
in by the caller; the code never reads a clock.

## Environment

- Language and version: Python 3.11
- Allowed dependencies: standard library only
- Test command: `./run_tests.sh` (must exit 0)
- No network access, no reading files outside this folder, no global state. Same input gives same output.

## Public interface

Implement exactly this, in `src/window_counter.py`. Names, argument order and types are fixed.

```python
class WindowCounter:
    def __init__(self, window_seconds: float, store) -> None:
        """store is a collaborator, see Collaborators."""

    def hit(self, key: str, now: float) -> int:
        """Record one event for key at time now; return the count inside the window."""

    def count(self, key: str, now: float) -> int:
        """Return the count inside the window without recording an event."""
```

## Data shapes

- `key`: non-empty string, at most 200 characters.
- `now`: seconds as a float, >= 0.
- `window_seconds`: float, > 0.

## Rules

- R1. The window for a call at time `now` is the interval `(now - window_seconds, now]`: open at the old end, closed at `now`.
- R2. `hit` records the event first, then counts, so its result is always at least 1.
- R3. `count` never changes what is stored.
- R4. Keys are independent of each other.
- R5. Events that can no longer fall inside any future window must be removed from the store, so the store does not grow without bound.
- R6. All event times are kept only in `store`; a second `WindowCounter` built on the same store sees the same events.

## Errors

| Situation | Required behaviour |
| --- | --- |
| `window_seconds` <= 0 | `ValueError` from `__init__` |
| `key` is empty or longer than 200 characters | `ValueError` |
| `key` is not a `str` | `TypeError` |
| `now` is negative | `ValueError` |

## Worked examples

All with `window_seconds=10`.

### Example 1

hit("a", 0.0) -> 1, then hit("a", 5.0) -> 2  (R2)

### Example 2

hit("a", 0.0), then hit("a", 10.0) -> 1  (R1: the event at 0.0 is exactly on the open end, so it is outside)

### Example 3

hit("a", 0.0), then hit("a", 9.999) -> 2

### Example 4

hit("a", 1.0), then count("b", 1.0) -> 0  (R4), and count("a", 1.0) -> 1 twice in a row (R3)

### Example 5

hit("", 1.0) -> ValueError

## Collaborators

`store` holds the event times. It has exactly two methods:

```python
def get(self, key: str) -> list[float]: ...   # returns [] for an unknown key
def put(self, key: str, values: list[float]) -> None: ...
```

A ready-made fake is in `starter/fake_store.py` (`FakeStore`). Take the store as the constructor
argument; do not import a store inside `src/`.

## Limits

100,000 calls to `hit` on one key with a window holding at most 1,000 events must finish in under 2 seconds.

## Deliverables

- `src/`: the implementation.
- `tests/`: your own tests. `tests/acceptance/` is provided and must not be edited.
- `SUBMISSION.md`: a report of what you did and the test results.

## Out of scope

Thread safety, persistence formats, a command line interface, logging.
