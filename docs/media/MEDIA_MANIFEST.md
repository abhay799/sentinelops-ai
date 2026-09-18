# SentinelOps Media Manifest

No rendered screenshot assets are currently committed. All screenshot entries are **PENDING CAPTURE** and the portfolio uses labelled placeholders. See [CAPTURE_GUIDE.md](CAPTURE_GUIDE.md) for the real-rendered capture procedure.

| Intended asset | Status | Source view | Scenario | Provenance | Real capture exists | Portfolio placement |
|---|---|---|---|---|---|---|
| `mission-control.png` | PENDING CAPTURE | Mission Control (`/`) | `safe-local-recovery` | LOCAL / SYNTHETIC / DETERMINISTIC | No | Control Center preview |
| `service-health.png` | PENDING CAPTURE | Service Health (`/services`) | `correlated-multi-signal` | LOCAL / SYNTHETIC / DETERMINISTIC | No | Optional expanded preview |
| `rca-intelligence.png` | PENDING CAPTURE | RCA Intelligence (`/rca`) | `competing-rca-hypotheses` | LOCAL / SYNTHETIC / DETERMINISTIC | No | Optional expanded preview |
| `rca-challenger.png` | PENDING CAPTURE | RCA Challenger (`/challenger`) | `adversarial-rca-challenge` | LOCAL / SYNTHETIC / DETERMINISTIC | No | Control Center preview |
| `sentinelguard.png` | PENDING CAPTURE | SentinelGuard (`/guard`) | `sentinelguard-rejection` | LOCAL / SYNTHETIC / DETERMINISTIC | No | Control Center preview |
| `safe-local-recovery.png` | PENDING CAPTURE | Recovery (`/recovery`) | `safe-local-recovery` | LOCAL SANDBOX / SYNTHETIC / DETERMINISTIC | No | Control Center preview |
| `investigation.png` | PENDING CAPTURE | Investigation (`/investigation`) | `competing-rca-hypotheses` | LOCAL / SYNTHETIC / DETERMINISTIC | No | Control Center preview |
| `system-status.png` | PENDING CAPTURE | System Status (`/system`) | `normal-operation` | LOCAL / SYNTHETIC / DETERMINISTIC | No | Optional expanded preview |
| `portfolio-home.png` | PENDING CAPTURE | Portfolio home | Not applicable | Static local portfolio presentation | No | Portfolio overview |

Any future status change requires a file in `ui/portfolio/public/media/` captured from the real rendered source view. It must never be used for image-generated, illustrated, or manually reconstructed UI media.
