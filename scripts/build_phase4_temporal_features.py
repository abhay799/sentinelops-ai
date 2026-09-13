from pathlib import Path

from sentinelops.features.builder import (
    load_events,
    load_topology,
)
from sentinelops.features.temporal import (
    build_temporal_service_features,
    validate_point_in_time,
)

events = load_events(
    Path(
        "data/telemetry/raw/"
        "phase4_capture.ndjson"
    )
)

topology = load_topology(
    Path("configs/topology.yaml")
)


features = build_temporal_service_features(
    events=events,
    topology=topology,
    short_seconds=60,
    medium_seconds=300,
)


validate_point_in_time(features)


output = Path(
    "data/processed/features/"
    "temporal_features_v1.parquet"
)

output.parent.mkdir(
    parents=True,
    exist_ok=True,
)

features.write_parquet(output)


print(
    "Temporal rows:",
    features.height,
)

print(
    "Temporal columns:",
    features.width,
)

print(
    "Services:",
    features[
        "service"
    ].n_unique(),
)

print(
    "Output:",
    output,
)

print()

print(
    "POINT-IN-TIME VALIDATION: PASSED"
)

print(
    "PHASE 4 TEMPORAL FEATURES: PASSED"
)