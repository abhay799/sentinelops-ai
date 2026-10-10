# Phase C C4 — Invalid-run and Replacement Policy

**Status:** preregistered before any Phase C registered run.

The registered v1 result distinguishes infrastructure invalidity from algorithmic outcome.

## Infrastructure-invalid runs

A registered run is infrastructure-invalid only when the run cannot be interpreted because of an execution-environment failure unrelated to the injected scenario. The allowed infrastructure-invalid reasons are:

- host sleep or a host-clock discontinuity/jump that invalidates timing;
- WSL restart or loss of the WSL execution environment;
- service death unrelated to the registered injection;
- harness crash that prevents completion of the run record/evidence chain.

Every such run remains in the ledger with its original run ID, seed, partition, scenario, evidence collected before failure, and explicit invalid reason. It is never deleted or rewritten as a successful run.

An infrastructure-invalid run is replaced by the **next unused reserved spare seed in the same scenario and same partition**, in ascending `spare_ordinal` order.

Exactly two spare seeds are reserved for each scenario/partition cell. If both are exhausted, execution for that cell stops; no ad-hoc seed is generated under the v1 protocol.

## Algorithmic outcomes are never replaced

The following are valid registered outcomes and are never grounds for a replacement run:

- missed detection;
- incorrect correlation;
- wrong RCA ranking/root-cause result;
- challenger disagreement;
- SentinelGuard block;
- remediation not authorized by the Guard;
- failed remediation;
- failed recovery verification.

These outcomes remain in the registered denominator.

## Separation from emergency cleanup

Emergency cleanup exists only to return the local environment to a safe state after a run. It is recorded separately, is never counted as remediation, and does not turn an algorithmic failure into a successful remediation.
