from __future__ import annotations

from pathlib import Path
from typing import Any

import networkx as nx
import yaml


class ServiceDependencyGraph:

    def __init__(self) -> None:
        self.graph = nx.DiGraph()

    @classmethod
    def from_topology_file(
        cls,
        path: Path,
    ) -> "ServiceDependencyGraph":

        instance = cls()

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            config = yaml.safe_load(file)

        topology = config["topology"]

        for service, details in topology.items():

            instance.graph.add_node(
                service
            )

            for dependency in details[
                "depends_on"
            ]:

                instance.graph.add_edge(
                    service,
                    dependency,
                )

        return instance

    def services(self) -> list[str]:
        return sorted(
            self.graph.nodes
        )

    def dependencies(
        self,
        service: str,
    ) -> list[str]:

        self._validate_service(
            service
        )

        return sorted(
            self.graph.successors(
                service
            )
        )

    def dependents(
        self,
        service: str,
    ) -> list[str]:

        self._validate_service(
            service
        )

        return sorted(
            self.graph.predecessors(
                service
            )
        )

    def downstream(
        self,
        service: str,
    ) -> list[str]:

        self._validate_service(
            service
        )

        return sorted(
            nx.descendants(
                self.graph,
                service,
            )
        )

    def upstream(
        self,
        service: str,
    ) -> list[str]:

        self._validate_service(
            service
        )

        return sorted(
            nx.ancestors(
                self.graph,
                service,
            )
        )

    def shortest_path(
        self,
        source: str,
        target: str,
    ) -> list[str]:

        self._validate_service(source)
        self._validate_service(target)

        try:
            return nx.shortest_path(
                self.graph,
                source=source,
                target=target,
            )

        except nx.NetworkXNoPath:
            return []

    def propagation_distances(
        self,
        failed_service: str,
    ) -> dict[str, int]:

        self._validate_service(
            failed_service
        )

        reverse_graph = (
            self.graph.reverse(
                copy=False
            )
        )

        distances = nx.single_source_shortest_path_length(
            reverse_graph,
            failed_service,
        )

        return {
            service: distance
            for service, distance
            in distances.items()
            if service != failed_service
        }

    def risk_propagation(
        self,
        failed_service: str,
        base_risk: float,
        decay: float = 0.6,
    ) -> dict[str, float]:

        distances = (
            self.propagation_distances(
                failed_service
            )
        )

        propagated = {}

        for service, distance in (
            distances.items()
        ):

            propagated[
                service
            ] = round(
                base_risk
                * (decay ** distance),
                6,
            )

        return propagated

    def impact_order(
        self,
        failed_service: str,
    ) -> list[str]:

        distances = (
            self.propagation_distances(
                failed_service
            )
        )

        return [
            service
            for service, _distance
            in sorted(
                distances.items(),
                key=lambda item: (
                    item[1],
                    item[0],
                ),
            )
        ]

    def validate(self) -> None:

        if not nx.is_directed_acyclic_graph(
            self.graph
        ):
            raise ValueError(
                "Service dependency graph "
                "contains a cycle"
            )

        if self.graph.number_of_nodes() == 0:
            raise ValueError(
                "Service dependency graph "
                "is empty"
            )

    def snapshot(
        self,
    ) -> dict[str, Any]:

        return {
            "nodes": [
                {
                    "service": service,
                }
                for service
                in sorted(
                    self.graph.nodes
                )
            ],

            "edges": [
                {
                    "source": source,
                    "target": target,
                }
                for source, target
                in sorted(
                    self.graph.edges
                )
            ],

            "node_count":
                self.graph.number_of_nodes(),

            "edge_count":
                self.graph.number_of_edges(),
        }

    def _validate_service(
        self,
        service: str,
    ) -> None:

        if service not in self.graph:
            raise KeyError(
                f"Unknown service: {service}"
            )