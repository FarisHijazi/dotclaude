# Writing an assignment a blind worker can finish

## From secret to neutral: one worked example

Private reality (stays in `.dc/PLAN.md`): a tool that watches a rival shop's prices and suggests our
own price just below theirs, never below our cost.

Bad piece: "Competitor undercut engine". The title is the project.

Good cut:

| Neutral title | What the worker builds | Secret left out and passed in later |
| --- | --- | --- |
| Tabular text extractor | pulls (key, number) pairs out of text using patterns it is given | the rival's page layout patterns |
| Bounded offset calculator | given a reference number, a floor and a step, returns the adjusted number | our cost floor, the undercut step |
| Change log with deduplication | stores (key, value, time) rows, skips repeats, answers "latest per key" | what the keys and values mean |
| Periodic task runner | calls a function every N seconds with retry and backoff | what the function does |

None of the four says "price", "competitor" or "shop". Each is something a course could set.

## A complete good assignment

```markdown
# Assignment: Bounded offset calculator

## Problem

Given a reference value, compute an adjusted value that sits a fixed step below the reference but
never below a floor. Values are amounts with two decimal places. The function is pure.

## Environment

- Language and version: Python 3.11
- Allowed dependencies: standard library only
- Test command: `./run_tests.sh` (must exit 0)
- No network access, no reading files outside this folder, no global state. Same input gives same output.

## Public interface

Implement exactly this, in `src/offset.py`.

    from decimal import Decimal

    def adjust(reference: Decimal, floor: Decimal, step: Decimal) -> Decimal:
        """Return the adjusted value for one reference value."""

## Data shapes

All three arguments and the result are `Decimal` with at most two decimal places, 0 <= value <= 1,000,000.

## Rules

- R1. The result is `reference - step` when that is greater than or equal to `floor`.
- R2. Otherwise the result is `floor`.
- R3. The result is always quantized to two decimal places, rounding half up.
- R4. When `reference` is below `floor`, the result is still `floor`.

## Errors

| Situation | Required behaviour |
| --- | --- |
| any argument is not a `Decimal` | raise `TypeError` |
| any argument is negative | raise `ValueError` with a message naming the argument |
| `step` is zero | allowed; result is `max(reference, floor)` |

## Worked examples

### Example 1
adjust(Decimal("10.00"), Decimal("7.00"), Decimal("0.50")) -> Decimal("9.50")  (R1)

### Example 2
adjust(Decimal("7.20"), Decimal("7.00"), Decimal("0.50")) -> Decimal("7.00")  (R2)

### Example 3
adjust(Decimal("7.50"), Decimal("7.00"), Decimal("0.50")) -> Decimal("7.00")  (R1, exactly at the floor)

### Example 4
adjust(Decimal("5.00"), Decimal("7.00"), Decimal("0.50")) -> Decimal("7.00")  (R4)

### Example 5
adjust(Decimal("-1.00"), Decimal("7.00"), Decimal("0.50")) -> ValueError mentioning "reference"

## Collaborators

None.

## Limits

None.

## Deliverables

- `src/`: the implementation.
- `tests/`: your own tests. `tests/acceptance/` is provided and must not be edited.
- `SUBMISSION.md`: as described in `HOW_TO_WORK.md`.

## Out of scope

Currency handling, batch processing, configuration loading.
```

Why it is good: the title is generic, the signature is exact, every rule is testable, the examples
cover the boundary (Example 3) and the error (Example 5), and nothing says what the numbers are.

## Common mistakes

| Mistake | What goes wrong | Fix |
| --- | --- | --- |
| "Handle errors appropriately" | worker picks a behaviour, you get surprises at wiring time | fill the Errors table: situation, exact behaviour |
| Rule with "etc." or "and so on" | the unstated cases are guessed | list every case, or give the general rule plus examples |
| Examples that only show the happy path | boundaries come back wrong | always include empty, boundary and error examples |
| Real-looking example data | leaks the domain | invent ordinary values: "alice", "item-17", "north" |
| Revealing field names (`competitor_price`) | leaks the domain | rename to what it is structurally: `reference_value` |
| "This will be used by the X service to ..." | leaks purpose and neighbours | delete it; describe only the inputs and outputs |
| Two assignments describing one shared shape in different words | the pieces do not fit | paste the same block from PLAN.md "Shared interfaces" into both |
| Assignment says "call the database" | worker cannot test it, or invents one | give an interface (`get(key)`, `put(key, value)`) and a dictionary-backed fake in `starter/` |
| One assignment with ten rules about three topics | too big, reveals too much | cut it into three |

## Fakes in `starter/`

A fake is the simplest thing that satisfies the interface: a class holding a dictionary or a list.
State the interface in the assignment's Collaborators section and tell the worker the file name. The
worker's code must take the collaborator as an argument, so that you can pass the real one when you
wire the project.

## Renaming and wiring back

Neutral names stay in the delivered code. You do not rename them afterwards. The meaning lives in
your wiring file, where a neutral function receives a secret value:

```python
adjusted = adjust(reference=their_price, floor=our_cost, step=settings.undercut_step)
```

That one line is the kind of code that is yours to write.
