# Step 27 RE2-TT adapter freeze

Date: 2026-10-04
Status: frozen before any Step 27 RCA method ranking or scoring.

## E3 candidate presence and chance

The frozen RE2-TT allowlist contains 45 official application services. A label-free candidate-membership check over the already-validated metric service vocabularies shows that exactly 39 of those 45 services are metric-visible in every one of the 90 RE2-TT cases. The set is constant across all cases.

The six frozen allowlist services absent from every TT metric case are: `ts-delivery-service`, `ts-food-delivery-service`, `ts-gateway-service`, `ts-station-food-service`, `ts-train-food-service`, and `ts-wait-order-service`.

E3 remains an order-preserving filter of each native ranking to the frozen 45-service allowlist; the allowlist itself is not changed. Because the six absent services cannot occur in any native metric-derived ranking, the effective E3 random-ranking candidate universe is the constant 39 metric-visible allowlisted services. Therefore Step 27 analytical Chance@5 is frozen as `5/39`, and ChanceAvg@5 as `15/(5*39)`.

No root-cause label or ranking accuracy was used for this determination.

## BARO/CIRCA SLI adapter

Pinned RCAEval uses `ts-ui-dashboard_latency` as the default Train Ticket SLI, but its generic CLI can replace that with the injected service's latency when available. Step 27 will not use that root-service-informed switch. The adapter freezes `sli="ts-ui-dashboard_latency"` for every TT case.

The previously audited pinned RCAEval revision `259ea4167160256a74ad30004aa3d96a998c846e` shows that BARO accepts but does not read `sli`, and CIRCA accepts it through `**kwargs` and does not read it. Thus this fixed SLI avoids ground-truth-informed adapter state without changing the pinned BARO/CIRCA computation.

mmBARO and mmCIRCA remain n/a under the frozen input contract.
