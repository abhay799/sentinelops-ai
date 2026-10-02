# Phase A Step 16 — unresolved-parent breakdown

**Date:** 2026-10-02  
**Suite:** RE2-OB  
**Policy:** unresolved parent services are never inferred.

Across all 90 RE2-OB cases, the trace-derived topology encountered 2,380
pre-injection child spans whose referenced parent span was absent. None of those
parent keys existed elsewhere in the full trace files, so the frozen
pre-injection-boundary ambiguity condition was never triggered. Their parent
service is therefore recorded as **unknown**.

Unresolved references by child service:

- checkoutservice: 42
- currencyservice: 725
- emailservice: 3
- frontend: 1,066
- paymentservice: 3
- productcatalogservice: 491
- recommendationservice: 50

Where the parent span was actually present, resolved parent-service counts were:

- checkoutservice <- frontend: 30,238
- currencyservice <- checkoutservice: 104,212
- currencyservice <- frontend: 2,443,728
- emailservice <- checkoutservice: 30,242
- paymentservice <- checkoutservice: 30,241
- productcatalogservice <- checkoutservice: 73,973
- productcatalogservice <- frontend: 3,919,133
- productcatalogservice <- recommendationservice: 602,095
- recommendationservice <- frontend: 602,116

The four application services with no trace-derived edges are explained by
telemetry coverage, not by guessed missing-parent identities:

- adservice: metric-present but trace-absent in all 90 cases.
- cartservice: metric-present but trace-absent in all 90 cases.
- shippingservice: metric-present but trace-absent in all 90 cases.
- redis: metric-present but trace-absent in all 90 cases.

Consequently those four services were retained as graph nodes but had no
trace-derived incident edges. The 2,380 unresolved references belong only to
the seven trace-observed services listed above; they do not provide evidence
that any unresolved parent was adservice, cartservice, shippingservice, or
redis.
