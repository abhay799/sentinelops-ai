# Step 26 RE2-SS Allowlist Preflight

Date: 2026-10-03
Status: PASS before any RE2-SS raw-data access.

Erratum E3.3 freezes the Sock Shop application-service candidate allowlist as:

- `front-end`
- `carts`
- `catalogue`
- `orders`
- `payment`
- `queue-master`
- `shipping`
- `user`

The same E3 section explicitly excludes database/infrastructure deployments,
including `carts-db`, `catalogue-db`, `orders-db`, `user-db`, `session-db`, and
`rabbitmq`.

This Step 26 preflight does not alter that list. After RE2-SS is downloaded,
checking the already-frozen allowlist against the benchmark ground-truth service
labels is permitted only as a validity/mapping check: every ground-truth root
must map to an already-admissible frozen candidate. That check may detect a
schema/name mismatch and trigger a stop, but it may not add, remove, rename, or
reweight candidates based on held-out outcomes. Any required protocol change
would require a dated amendment and would invalidate proceeding silently.

No RE2-SS raw case, ranking, metric, or ground-truth label was read for this
preflight record.
