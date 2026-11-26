# Assignment: <<neutral title, e.g. "Interval merger">>

## Problem

<<3-8 sentences. What goes in, what comes out, stated as a stand-alone exercise. No product, customer, company or purpose.>>

## Environment

- Language and version: <<e.g. Python 3.11>>
- Allowed dependencies: <<"standard library only", or an exact list>>
- Test command: `./run_tests.sh` (must exit 0)
- No network access, no reading files outside this folder, no global state. Same input gives same output.

## Public interface

Implement exactly this, in `src/<<file name>>`. Names, argument order and types are fixed.

```<<language>>
<<exact signatures with types and a one-line docstring each>>
```

## Data shapes

<<every structure that crosses the interface: fields, types, units, allowed ranges, whether it may be empty or null>>

## Rules

Numbered, one behaviour per rule, each one testable.

- R1. <<...>>
- R2. <<...>>
- R3. <<...>>

## Errors

| Situation | Required behaviour |
| --- | --- |
| <<bad input ...>> | <<raise ValueError with message containing "...">> |

## Worked examples

### Example 1

<<input>> -> <<output>>  (shows R<<n>>)

### Example 2

<<input>> -> <<output>>

### Example 3

<<an edge case: empty input>>

### Example 4

<<an edge case: boundary value>>

### Example 5

<<an error case>>

## Collaborators

<<"None." or: things this code calls but does not own. Give the exact interface of each and say which file in `starter/` holds a ready-made fake. The worker never sees the real one.>>

## Limits

<<input sizes and how fast it must be, e.g. "up to 100,000 items in under 1 second". Write "None." if it does not matter.>>

## Deliverables

- `src/`: the implementation.
- `tests/`: your own tests. `tests/acceptance/` is provided and must not be edited.
- `SUBMISSION.md`: as described in `HOW_TO_WORK.md`.

## Out of scope

<<things the worker might be tempted to add: CLI, logging, persistence, configuration loading ...>>
