---
name: Deep data analysis preference
description: User wants exhaustive, deep-dive data analysis - find all issues, keep going, don't stop at surface level
type: feedback
originSessionId: 8ecaec23-94b6-484c-91e4-87f62ef545f5
---
When exploring data, go extremely deep. Don't stop at basic counts and schema checks. Dig into:
- Value distributions, outliers, duplicates
- Cross-table joins and referential integrity
- Temporal patterns, gaps, anomalies
- Enum/category inconsistencies
- Data lineage issues

**Why:** User has a large backlog of analysis work and wants thorough exploration that surfaces non-obvious issues like the financial 100x multiplier or Jaco ID changes.

**How to apply:** When given a data exploration task, keep going until exhausting all angles. Write findings as markdown docs. Create reusable scripts for repeated operations.
