# Phase A Step 13 Detector Investigation Resolution

Date: 2026-10-03
Repository checkpoint before amendment: b007522132d391cb32b5dc0dd206406960f5f77d

**Status: DOCUMENTATION-ONLY RESOLUTION AFTER RE2-OB DIAGNOSTIC REVIEW.**
This amendment resolves the Step 13 *investigation stop* only. It does not
reclassify detector v1 as successful, change detector/scoring logic, or authorize
RE2-SS/RE2-TT evaluation by itself.

The original Step 13 smoke result remains unchanged: on
`re2ob_checkoutservice_cpu_1`, 350/360 normal-evaluation timestamps alerted
(97.22%), 721/721 fault timestamps alerted (100%), and detection delay was zero.
The historical `STEP13_DIAGNOSIS.md` stop statement is retained as provenance.

A read-only follow-up investigation verified that the implementation matches
the frozen specification: calibration uses the first 50% of pre-injection
rows; z-score and EWMA use threshold 2.5; EWMA alpha is 0.30; Isolation Forest
uses contamination 0.10 and random_state 42; service anomaly is a 2-of-3 vote;
system alert is positive when any service is anomalous; and a normal/fault
window is positive when any timestamp in that window alerts. Detector code
does not consume the ground-truth root-cause service, fault label, or case ID
to generate predictions. No implementation or ground-truth leakage bug was
found in this review.

Step 15 reproduces the same behavior across all 90 RE2-OB cases. Frozen v1 has
window confusion TP=90, FP=90, TN=0, FN=0: normal-window false positives are
90/90, fault-window true positives are 90/90, precision is 0.5, recall is 1.0,
and window F1 is 0.6666666667, exactly equal to the saved always-alert baseline.
At timestamp level, 28,781 of 32,400 normal-evaluation timestamps are false
positives, an 88.83% false-positive rate; fault timestamp recall is 99.86%.

The continuous system score is also saturated. The maximum system anomaly score
is exactly 1.0 in 49/90 normal windows and 86/90 fault windows, with both equal
to 1.0 in 48/90 cases. The median normal-window and fault-window maxima are both
1.0. This is consistent with the frozen aggregation/normalization design and
explains why binary window detection collapses toward always-alert behavior.

Detector v1 is retained unchanged as a **negative baseline result**: it is
highly sensitive and has unusably poor specificity at the frozen system/window
aggregation level. No threshold, alpha, contamination, voting rule, calibration
split, normalization rule, service aggregation, system aggregation, or window
rule is tuned from RE2-OB outcomes.

This evidence clears the historical Step 13 requirement to investigate a
suspicious 100% detection result because the behavior is reproduced across the
full 90-case RE2-OB evaluation and checked against the frozen implementation.
It does **not** establish detector success or generalization, and it does not
clear any other stop rule. RE2-SS and RE2-TT remain untouched. Never push.
