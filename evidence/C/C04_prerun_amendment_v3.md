# Phase C C6 Start Gate — Amendment 3

**Amendment time (UTC):** `2026-10-11T16:41:10Z`
**State:** pre-result; no registered run executed, no registered result exists.

## Cause

The v2 checklist/freeze did not include the unattended TRAIN loop or a non-registry executor validation mode. Amendment 3 adds those engineering controls before registered run 1 without changing the frozen registry, registered seeds, partition assignments, scenario definitions, Guard/remediation thresholds, registered analysis metrics, or the C7 TRAIN-baseline-only detector-fit rule.

## Runtime completeness closure

The registered TRAIN execution surface was conservatively traced across direct and transitive local imports, scripts executed by subprocess, config loaders, execution/remediation adapters, registered analysis, detector scripts, local demo-service runtime, compose files, and the TRAIN loop. The closure contains **103 repository files**. Every file below is required to be SHA-256 covered by `C04_prerun_freeze_v3.json`; no unfrozen repository file is permitted to execute on the registered TRAIN path.

| File | SHA-256 | Covered by v2 |
|---|---|---|
| `configs/anomaly.yaml` | `2b57a76a1cd6514574f98e02a82691dfd7c9385cba0984df7be896573911dbb0` | yes |
| `configs/app.yaml` | `c0cc053ca987c2b5e206d4f3d764c6aeb89c260467efa4881a8efa16d83e7b47` | NO — newly covered by v3 |
| `configs/chaos_bad_deployment_v1.yaml` | `62e22a74c6714b505e4c8f91e707ba0b94fada5559b253ac3a62d2a01d291c2e` | yes |
| `configs/chaos_scenarios_v1.yaml` | `91de2d7235ce1736150a1dfb7997f61a6ec9c4e84622ea143833955fa9291983` | yes |
| `configs/counterfactual.yaml` | `54f9c470b5a91aa7587a54f30fb2ac0eb55fa2c6a641281aa48784fb93784c96` | NO — newly covered by v3 |
| `configs/evaluation.yaml` | `41fa0c7862a49dfc259faf96bf7673ab5571f80fca1b8163683668beda807adb` | NO — newly covered by v3 |
| `configs/execution.yaml` | `0598dd0ba5a41a5c014a73298afc977c82b527232f085f057cda3a1a2f69434e` | NO — newly covered by v3 |
| `configs/failure_prediction.yaml` | `2e0bad04e73e79fda13bd0e69dabfd1a6de948258062d54f2e876a5b46659bb9` | NO — newly covered by v3 |
| `configs/failure_scenarios.yaml` | `0d39ccee98335494045db5bbc9638c15d122d38d9d46565ab7e177949bdb4797` | NO — newly covered by v3 |
| `configs/features.yaml` | `de35ba01819479fcc0bd72ceb7b4ef5918cc54e50d7cbda347b82d9462c78d13` | NO — newly covered by v3 |
| `configs/graph.yaml` | `aa0a91b611a6fa6ec9b2547702bbdf3ea4c3cd7ed527c8a77ff3599075bc2a19` | NO — newly covered by v3 |
| `configs/incident_correlation.yaml` | `14ba3edb907228bc131ed6f2c6ec6b819fcff82ba60ac29d5f28e722567149ff` | NO — newly covered by v3 |
| `configs/incident_priority.yaml` | `e71e5c29a391a2074c1d6aee01a4394cb59efaf91c491cc1ee4a88f53ca3f78a` | NO — newly covered by v3 |
| `configs/investigation.yaml` | `765600f700e1392b968df7a62c272d0dd38d888126975021a940191bf2958c61` | NO — newly covered by v3 |
| `configs/rca.yaml` | `507a6dd76dd89b72d08fadab98a7fd8a063ef6a7488e90b08878526420a3c32d` | NO — newly covered by v3 |
| `configs/rca_challenger.yaml` | `849bed102fd4ce4226745c620ca2af63d3d76402e6e8eb4d2bd562b798aec8d5` | NO — newly covered by v3 |
| `configs/remediation.yaml` | `ac98a07fa1b43f3cf9995ae1970bc2970670c72eeae47e1135eca136d616b447` | yes |
| `configs/security.yaml` | `6def1470d36354b0540719a7e5784b44ec4ec3464ca8d6bd6e1d50efa60d2e7d` | NO — newly covered by v3 |
| `configs/sentinelguard.yaml` | `6e4946041c4eddad25969d932e04a9367b3bf08c264c7e6a90cf66a0ce399a96` | yes |
| `configs/services.yaml` | `d25130550191882b62d804a0cb3755d00b10925b966a7bee75fa5144ad652932` | NO — newly covered by v3 |
| `configs/slo_business_impact.yaml` | `5a84762d17e2a6c8de8a4926883d08e1b77b221762f7b32319cbb70b55df2492` | NO — newly covered by v3 |
| `configs/telemetry.yaml` | `31005a70773645a09d6a42975eaa3caf3aa206e76b28a66e03de75d0cacf34e6` | NO — newly covered by v3 |
| `configs/topology.yaml` | `aa0d059cba9e15222b0e4ed4bd375aa35fd13e5528e57ccb892066a7034b07d7` | NO — newly covered by v3 |
| `docs/design/chaos_harness_v1.md` | `52a37f8791b71e782d335b42dde9ce5bc94fa3564c9fb6483d4fbf59f947318b` | yes |
| `evidence/C/C04_detector_fit_procedure.md` | `75915cf22008a990b9a108fffc32ca9d80b0b530090704869658a4ba42b861de` | yes |
| `evidence/C/C04_feature_schema.json` | `477c38f1ff1a31ec1c132ca7dc90eda445c7e34f2de8aed507aaf716af6ea4db` | yes |
| `evidence/C/C04_invalid_run_policy.md` | `27ee261541c7164cd2a8be9f51f3efba9b92a27f4ca4fe0252f82f37d247c0e5` | yes |
| `evidence/C/C04_preregistration.md` | `3f451e973e4f40aeba7248348b0371259eb9d07c098ccd94d3fabae49c907ae8` | yes |
| `evidence/C/C04_run_registry.json` | `e88ff4b8363a7cfc89d709175d50127a46a1880290961a66c694d7c64b79df07` | yes |
| `infra/docker-compose.core.yml` | `fd402bc2c3b10579720af5f7b4145785b4c606bbbc37311373b989003f227138` | NO — newly covered by v3 |
| `infra/docker-compose.kafka.yml` | `2fd3e0ba8207c388e4a9c70a3c348cff61f541109a515357135e0de594762fbc` | NO — newly covered by v3 |
| `infra/docker-compose.observability.yml` | `81edafdb79ed2ccc98142c0df3d181a046689ce6f9aba17c5c3f1a4e186d3dd9` | NO — newly covered by v3 |
| `infra/docker-compose.phase2.yml` | `d74a154cd98e92316e4ac8e84eee8f70419dfd10ad160342e84fbc89ab8c94b3` | NO — newly covered by v3 |
| `pyproject.toml` | `8a64f091b2fede2ba51cb1d692e1db8887d6fec05a29ac72bd6de541714980ad` | NO — newly covered by v3 |
| `scripts/build_phase10_early_warning.py` | `f705e260c1347a7a01e72a750c26b1d48394b3190f39e7e4e49fb28b5715b75a` | NO — newly covered by v3 |
| `scripts/build_phase11_counterfactual.py` | `6e7c62e448f281410fc6819ab6b723b4711b568109cb63f9bdc4d511eae07952` | NO — newly covered by v3 |
| `scripts/build_phase11_counterfactual_summary.py` | `383ef3b79154b04645e0d4ca0366ef62bababb942550a21260dc4afd03ed7b91` | NO — newly covered by v3 |
| `scripts/build_phase12_incident_priority.py` | `65d982caca396961846fe87c81b6c513129746a9cf2a47d54606db4a25890fba` | NO — newly covered by v3 |
| `scripts/build_phase12_service_impact.py` | `5bf38aeeeb7a642003481df29cd2d9f47d08fc6b055c95a25b64f871cb64ac8f` | NO — newly covered by v3 |
| `scripts/build_phase13_remediation.py` | `b73b890d2a77cc6292324fb03da46011452ad0250a1f86da541fb638bbf2d439` | NO — newly covered by v3 |
| `scripts/build_phase14_approval_queue.py` | `dd329c62fe9d2d292fbad08356be3d575a411230c58e7160159e5659c8c707fc` | NO — newly covered by v3 |
| `scripts/build_phase14_execution_requests.py` | `482b0f2cc549bea81182d165e3be3546e7bed86ed69f1b196050aa3d461e9a24` | NO — newly covered by v3 |
| `scripts/build_phase4_temporal_features.py` | `aeef3bce1a57cde16e82aa45f3f19750ace8b932ef850a7670665308107f211e` | NO — newly covered by v3 |
| `scripts/build_phase6_graph.py` | `789c0de4d518d986498beb71060906feb5492537f4e44d13a458ad99508f9dd9` | NO — newly covered by v3 |
| `scripts/build_phase7_incident_intelligence.py` | `34a2d90b28da395336b5b10a1e842b269bfcfabe25878701f6bd8f8b7210ed46` | NO — newly covered by v3 |
| `scripts/build_phase7_incidents.py` | `2cafeab1ed88224e0b662b47f467e4abc6e1a70e13b42aae05abca1fcfc8911d` | NO — newly covered by v3 |
| `scripts/build_phase8_rca.py` | `b01f29e66d635643de81d37912b6ed62179c468a20071d237ff5544c8d515950` | NO — newly covered by v3 |
| `scripts/build_phase8_rca_summary.py` | `948980eb19ec1d9908e93985dbabc7c95fe825f9875aae9fa7ddbb014fcbfc93` | NO — newly covered by v3 |
| `scripts/build_phase9_causal_disposition.py` | `b37d917950642260aa69ea3d5702165482a31e2544813ffdfd0a522295f5a366` | NO — newly covered by v3 |
| `scripts/build_phase9_challenger.py` | `ac4ef069c22354fb10267b11ea72238037dfc734bfed6afc77f25680ad0befdb` | NO — newly covered by v3 |
| `scripts/execute_phase14_request.py` | `f723f42de58b40386fcdba389d57070a14864bdf6d75c4a09e955f4f9aa13343` | NO — newly covered by v3 |
| `scripts/phase14_approve.py` | `c83ad4b270e27eb52ee1edfe607611b8313b36222ce438b5c9404838eacce7c6` | NO — newly covered by v3 |
| `scripts/phase5_frozen_detector.py` | `121b5287f58e272945c1b948c2180c29de2189900e1908c21ca1fdbc4e49aeda` | yes |
| `scripts/phase_c06_run_registered.py` | `4e46f5f30767ccef263cf0a1e69d4d8678e832bb8a752938a92597b85ea824bc` | yes |
| `scripts/phase_c06_train_loop.py` | `f3ea5aa01161bbedb726bc04aa4cec4f73fe00957af8ef3f7ce858ce4353d3cc` | NO — newly covered by v3 |
| `scripts/phase_c_registered_analysis.py` | `edddb37238599fae52d02b33f85e72c20277510ef0b0f783cb8d7be366fdec2b` | yes |
| `scripts/train_phase10_predictor.py` | `ee388752e176298b20150a36374324ef38708dc2ca20c92e02bb6bd9a02f1fb3` | NO — newly covered by v3 |
| `scripts/train_phase5_anomaly.py` | `41ee6538b96a0a8e32d3c5a9f4a9d9410f60aceddd062a9ec5c5f224e6f91a1e` | NO — newly covered by v3 |
| `services/auth/Dockerfile` | `5ccd67a514ff01df2aef1a00a537eac1675f19be9a0ef3b22dd098eefbc5e42b` | NO — newly covered by v3 |
| `services/auth/app.py` | `8b0ef9e866148e935a2510a55b53c4d3b42dd18ba8e939e5b53d3629562cdb4a` | NO — newly covered by v3 |
| `services/common/runtime.py` | `c6954a7d39a534879745a1486d71c5e9029fae3127e8b1ee130e47a2dd7f74dc` | NO — newly covered by v3 |
| `services/gateway/Dockerfile` | `6b26b20dc9ee2b49d7969a73b718be6caf46d95d1becb36497b7f9cf59b72df9` | NO — newly covered by v3 |
| `services/gateway/app.py` | `8b0ef9e866148e935a2510a55b53c4d3b42dd18ba8e939e5b53d3629562cdb4a` | NO — newly covered by v3 |
| `services/inventory/Dockerfile` | `a717e165d89690e715f36c521d322553f88ca9cf1caf90529c0693c30571fa86` | NO — newly covered by v3 |
| `services/inventory/app.py` | `8b0ef9e866148e935a2510a55b53c4d3b42dd18ba8e939e5b53d3629562cdb4a` | NO — newly covered by v3 |
| `services/notification/Dockerfile` | `988231e7d9c92539a77a8f0184d287f643582247229880f71f129bf90e8c4946` | NO — newly covered by v3 |
| `services/notification/app.py` | `8b0ef9e866148e935a2510a55b53c4d3b42dd18ba8e939e5b53d3629562cdb4a` | NO — newly covered by v3 |
| `services/order/Dockerfile` | `ad32ecb2eeb3eaa75deac7df11d7c2e7b7b53ca6a48ba2e5d614443fddb1feb0` | NO — newly covered by v3 |
| `services/order/app.py` | `8b0ef9e866148e935a2510a55b53c4d3b42dd18ba8e939e5b53d3629562cdb4a` | NO — newly covered by v3 |
| `services/payment/Dockerfile` | `2d6b8a9d9143a7a647377045f5ebf02d65c324cc59ea14bc26c09afec34f95a6` | NO — newly covered by v3 |
| `services/payment/app.py` | `8b0ef9e866148e935a2510a55b53c4d3b42dd18ba8e939e5b53d3629562cdb4a` | NO — newly covered by v3 |
| `services/requirements.txt` | `3e968d351f00c30b49a5fdd3c43d7cd68d66e3524a6070b4891c8975af1ae0f9` | NO — newly covered by v3 |
| `services/user/Dockerfile` | `6f26a4a4ec456fe0f63c89cf73d8028385bb058d90c04f4ea3fe50e17ccb8a8f` | NO — newly covered by v3 |
| `services/user/app.py` | `8b0ef9e866148e935a2510a55b53c4d3b42dd18ba8e939e5b53d3629562cdb4a` | NO — newly covered by v3 |
| `src/sentinelops/anomaly/detectors.py` | `ee09e798f753132e019353d69d65207f834f611577c22066d760e670696c499f` | NO — newly covered by v3 |
| `src/sentinelops/anomaly/frozen_detector.py` | `6913ce5d3bd69958533889286144c5eaa136a45f383d2e21d222ecd327fcf267` | yes |
| `src/sentinelops/chaos/analysis.py` | `08c4aca0353959eeaf5e4d09d5d643b02b2314e579cf535e38a0b210a6657de8` | yes |
| `src/sentinelops/chaos/dry_run_stages.py` | `f415e4e569529030c69a06178ba82e8167273638313f28f31e86e3f8ad881508` | yes |
| `src/sentinelops/chaos/ground_truth.py` | `d98bb1efe1a4440383b95fced2f1dafa3e511a6ab809262f76357a7eb16d4ecf` | yes |
| `src/sentinelops/chaos/harness.py` | `873faf2c6357cbed67f4988c6bcee6398cd25d97581228be22f9ed7ed76c832c` | yes |
| `src/sentinelops/chaos/registered_harness.py` | `926e03ea54636eb308a2d097b87e66efae8f2c3bd694a043e6a072d911892111` | yes |
| `src/sentinelops/chaos/schema.py` | `874a2f31fb42c55754fc43096c42a677d24a59f1b098ba3d46a4ba59ec0a8ad5` | yes |
| `src/sentinelops/chaos/stage_events.py` | `1c4110ba26cb96dfc4a064d405c6043fd9dc56ea63fc89a0e76c1b92bb49613a` | yes |
| `src/sentinelops/counterfactual/engine.py` | `07b825c5e439fe2fe4893bf463e992ec0df7f07fe0d155a4167e1c7cd50c59c0` | NO — newly covered by v3 |
| `src/sentinelops/counterfactual/ranking.py` | `a543a74080879204ae6d534e8f9584966e196dc97ee39822e21415eb9c70289a` | NO — newly covered by v3 |
| `src/sentinelops/counterfactual/validation.py` | `20028fcdf6aefa556603583de2793b28e144cd87be923cb0ae99932de36560e5` | NO — newly covered by v3 |
| `src/sentinelops/execution/gate.py` | `3d076563eec371e28e66daa7c280b05219539b98a6eb81d5cefdf333d324a982` | NO — newly covered by v3 |
| `src/sentinelops/execution/runtime.py` | `384263f1a257ee626d9db9619db6872bb26dfa7d88f9a514ce6ea9923011dc50` | NO — newly covered by v3 |
| `src/sentinelops/features/builder.py` | `2fb7a77f4461d9b6108fa5878bc6e2ef924dd065dbae207bd878736cf2072bba` | NO — newly covered by v3 |
| `src/sentinelops/features/temporal.py` | `838078f571f9112d9a8a6c862212ca94f62740e48955d481d1828f880e9fc1e9` | NO — newly covered by v3 |
| `src/sentinelops/graph/service_graph.py` | `45616c1d3456caf3314019f637496774333426f841d965e725c1484ae03e3914` | NO — newly covered by v3 |
| `src/sentinelops/impact/engine.py` | `c86fbd8898e99cd0a9709cda9bd9fdfb9a4503f263538873e21f3ae3c1c8df23` | NO — newly covered by v3 |
| `src/sentinelops/impact/prioritization.py` | `e469653339dadc528ec9954268018887e387ede48d03dbb50bf7026987618356` | NO — newly covered by v3 |
| `src/sentinelops/incidents/correlator.py` | `e7fb0a3e36b64b633d655b8e6b13f0d4a39c259395ca7fbcec231c9daa913c4c` | NO — newly covered by v3 |
| `src/sentinelops/incidents/intelligence.py` | `ef61cb750439719f954ff09a96019cd565e1180b82df26a389d2c74316ab4221` | NO — newly covered by v3 |
| `src/sentinelops/prediction/early_warning.py` | `cbfc7c2d90e2c8b3d3356e7b34096c669dab563c19b00e22bc56639d0f62d1d3` | NO — newly covered by v3 |
| `src/sentinelops/prediction/evaluation.py` | `5d9f995ea28693449643aaea397d17e83629e3bd0d1dfc6a4d56d478b378dfc4` | NO — newly covered by v3 |
| `src/sentinelops/rca/causal.py` | `c96c268da6dc2eef4329bf9f652541b8b320557af3f64306d926282206277410` | NO — newly covered by v3 |
| `src/sentinelops/rca/challenger.py` | `e759d98add33feb2d0094e5461a60468619b03e6912f5f100eac16373e2baf9f` | NO — newly covered by v3 |
| `src/sentinelops/rca/engine.py` | `e11c073d73fea2f2c47a7598a382ef1a36f44ff9b81986307f44864ec3e05525` | NO — newly covered by v3 |
| `src/sentinelops/rca/validation.py` | `e586a32426f450c5e00d7ef4883684fcfb0132919b1a0ba9c1c8c27b76dad099` | NO — newly covered by v3 |
| `src/sentinelops/remediation/planner.py` | `ce2fde2c1d454bc233ffb455df92f0f642e9b2685024d3581de80b4d3dfecac5` | NO — newly covered by v3 |
| `src/sentinelops/remediation/sentinelguard.py` | `f965dde70defdf5e36cb81e61770c694d5ec47ace06dfcb3ef9c9ca9ca5c21a1` | NO — newly covered by v3 |

**Not covered by v2:** 81 files. These 81 paths are not staged as code changes merely to freeze them; v3 records their existing reviewed bytes by SHA-256.

- `configs/app.yaml`
- `configs/counterfactual.yaml`
- `configs/evaluation.yaml`
- `configs/execution.yaml`
- `configs/failure_prediction.yaml`
- `configs/failure_scenarios.yaml`
- `configs/features.yaml`
- `configs/graph.yaml`
- `configs/incident_correlation.yaml`
- `configs/incident_priority.yaml`
- `configs/investigation.yaml`
- `configs/rca.yaml`
- `configs/rca_challenger.yaml`
- `configs/security.yaml`
- `configs/services.yaml`
- `configs/slo_business_impact.yaml`
- `configs/telemetry.yaml`
- `configs/topology.yaml`
- `infra/docker-compose.core.yml`
- `infra/docker-compose.kafka.yml`
- `infra/docker-compose.observability.yml`
- `infra/docker-compose.phase2.yml`
- `pyproject.toml`
- `scripts/build_phase10_early_warning.py`
- `scripts/build_phase11_counterfactual.py`
- `scripts/build_phase11_counterfactual_summary.py`
- `scripts/build_phase12_incident_priority.py`
- `scripts/build_phase12_service_impact.py`
- `scripts/build_phase13_remediation.py`
- `scripts/build_phase14_approval_queue.py`
- `scripts/build_phase14_execution_requests.py`
- `scripts/build_phase4_temporal_features.py`
- `scripts/build_phase6_graph.py`
- `scripts/build_phase7_incident_intelligence.py`
- `scripts/build_phase7_incidents.py`
- `scripts/build_phase8_rca.py`
- `scripts/build_phase8_rca_summary.py`
- `scripts/build_phase9_causal_disposition.py`
- `scripts/build_phase9_challenger.py`
- `scripts/execute_phase14_request.py`
- `scripts/phase14_approve.py`
- `scripts/phase_c06_train_loop.py`
- `scripts/train_phase10_predictor.py`
- `scripts/train_phase5_anomaly.py`
- `services/auth/Dockerfile`
- `services/auth/app.py`
- `services/common/runtime.py`
- `services/gateway/Dockerfile`
- `services/gateway/app.py`
- `services/inventory/Dockerfile`
- `services/inventory/app.py`
- `services/notification/Dockerfile`
- `services/notification/app.py`
- `services/order/Dockerfile`
- `services/order/app.py`
- `services/payment/Dockerfile`
- `services/payment/app.py`
- `services/requirements.txt`
- `services/user/Dockerfile`
- `services/user/app.py`
- `src/sentinelops/anomaly/detectors.py`
- `src/sentinelops/counterfactual/engine.py`
- `src/sentinelops/counterfactual/ranking.py`
- `src/sentinelops/counterfactual/validation.py`
- `src/sentinelops/execution/gate.py`
- `src/sentinelops/execution/runtime.py`
- `src/sentinelops/features/builder.py`
- `src/sentinelops/features/temporal.py`
- `src/sentinelops/graph/service_graph.py`
- `src/sentinelops/impact/engine.py`
- `src/sentinelops/impact/prioritization.py`
- `src/sentinelops/incidents/correlator.py`
- `src/sentinelops/incidents/intelligence.py`
- `src/sentinelops/prediction/early_warning.py`
- `src/sentinelops/prediction/evaluation.py`
- `src/sentinelops/rca/causal.py`
- `src/sentinelops/rca/challenger.py`
- `src/sentinelops/rca/engine.py`
- `src/sentinelops/rca/validation.py`
- `src/sentinelops/remediation/planner.py`
- `src/sentinelops/remediation/sentinelguard.py`

## Added controls

- `scripts/phase_c06_train_loop.py` walks frozen TRAIN registry order, skips completed runs, never reruns a completed run, records interruption state, applies same-scenario TRAIN spare replacement, and stops when both preregistered spares are exhausted.
- `--status` reports primary accounting, spare use, active run and PID state. `--detach` uses a new session, persistent log and PID file.
- The registered executor now has a non-registry validation mode. It rejects any validation seed colliding with a primary registered seed or any reserved spare, and its outputs are `classification=non_registry` with `registered_result_eligible=false`.
- Restart/interruption and infrastructure-invalid logic were tested only with non-registry fixtures.

## Verification before v3 freeze

- New C6 targeted tests: **12 passed**.
- Requested Guard/Phase 13/Phase 14/C6 suite: **33 passed**.
- Non-registry executor validation: latency, errors and bad-deployment rollback each passed schema validation, UTC timestamp ordering and full-chain validation; collision count 0.
- Environment: Docker usable inside WSL; ports 8100–8106 were free before Phase 2 start and all seven `/ready` endpoints passed afterward with telemetry connected; Docker health reached healthy for all seven.
- Clock sample: WSL minus Windows = **-2243 ms**.
- Disk sample: **934G available** of 1007G.
- Registered evidence files: **0**; registered work files: **0**; registered control files: **0**.

## Registered execution gate

No registered TRAIN execution is authorized by this amendment itself. `freeze/C-prerun-v3` must be committed, pushed, and fresh-clone hash-verified before the user gives a separate GO.
