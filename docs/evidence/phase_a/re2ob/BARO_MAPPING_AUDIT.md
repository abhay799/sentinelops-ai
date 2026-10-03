# BARO Feature-to-Service Mapping Audit

Date: 2026-10-03
Scope: RE2-OB saved BARO evidence only; no rerun or fix.

The Phase A harness converts each BARO raw feature name to a service with:
`feature.split("_")[0].replace("-db", "")`, then keeps first occurrence order to
form the native service ranking. E3 is an order-preserving filter over that
service ranking.

Across all 90 BARO case files:
- reconstructed native mapping mismatches: 0.
- reconstructed E3 projection mismatches: 0.
- duplicate native-service rankings: 0.
- preprocess candidate-count mismatches: 0.
- raw BARO features containing `-db`: 0.

The mapped native services are the 11 E3 application services plus
`frontend-external`. Thus the current RE2-OB BARO mapping does not exercise the
`-db` normalization branch, and no evidence of service-label collapse or
mis-mapping was found.

Machine-readable evidence: `baro_mapping_audit.json`.
No mapping rule, ranking, filtering, score, or metric changed. Never push.
