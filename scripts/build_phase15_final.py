import json
from pathlib import Path

from sentinelops.investigation.llm import (
    DeterministicGroundedProvider,
)

from sentinelops.investigation.orchestrator import (
    InvestigationOrchestrator,
)

from sentinelops.investigation.validation import (
    validate_final_investigation,
)


EVIDENCE = Path(
    "data/processed/investigation/"
    "evidence_bundle_v1.json"
)

RETRIEVAL = Path(
    "data/processed/investigation/"
    "retrieval_v1.json"
)

OUTPUT = Path(
    "data/processed/investigation/"
    "final_investigation_v1.json"
)


evidence = json.loads(
    EVIDENCE.read_text(
        encoding="utf-8"
    )
)

retrieved = json.loads(
    RETRIEVAL.read_text(
        encoding="utf-8"
    )
)


provider = (
    DeterministicGroundedProvider()
)

orchestrator = (
    InvestigationOrchestrator(
        provider
    )
)


report = orchestrator.run(
    evidence,
    retrieved,
)


errors = validate_final_investigation(
    report
)

if errors:

    raise RuntimeError(
        "Final investigation validation "
        "failed:\n"
        + "\n".join(errors)
    )


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT.write_text(
    json.dumps(
        report,
        indent=2,
        default=str,
    ),
    encoding="utf-8",
)


print()
print("=" * 80)
print(
    " SENTINELOPS AI - PHASE 15 MULTI-AGENT INVESTIGATION"
)
print("=" * 80)

print(
    "Incident:",
    report[
        "incident_id"
    ],
)

print(
    "Evidence sources:",
    report[
        "evidence_source_count"
    ],
)

print(
    "Retrieved sources:",
    len(
        report[
            "retrieved_sources"
        ]
    ),
)

print(
    "LLM provider:",
    report[
        "grounded_generation"
    ][
        "provider"
    ],
)

print(
    "Agent RCA confirmation:",
    report[
        "safety"
    ][
        "root_cause_confirmed_by_agent"
    ],
)

print(
    "Agent execution authority:",
    report[
        "safety"
    ][
        "agent_execution_authority"
    ],
)

print()
print(
    "PHASE 15 MULTI-AGENT ORCHESTRATION: PASSED"
)
