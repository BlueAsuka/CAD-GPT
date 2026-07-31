"""Fixed-order Python graph rules for the supported gearbox topology.

Rules generate components and connections only. Calculations later add loads and
gear parameters, layout adds coordinates, and the CAD package creates geometry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from gearen.design_graph import DesignGraph
from gearen.models import GearboxRequirement


@dataclass
class DesignContext:
    """Small mutable context used only by this gearbox grammar."""

    requirement: GearboxRequirement
    applied_rule_ids: list[str] = field(default_factory=list)
    topology_complete: bool = False


@dataclass(frozen=True)
class RuleResult:
    """Observable outcome from applying one topology rule."""

    rule_id: str
    applied: bool
    added_nodes: tuple[str, ...] = ()
    message: str = ""


class DesignRule(ABC):
    """Base interface for one explicit product-topology rule."""

    rule_id: str
    description: str

    @abstractmethod
    def matches(self, graph: DesignGraph, context: DesignContext) -> bool:
        """Return whether the rule can add its topology exactly once."""

    @abstractmethod
    def apply(self, graph: DesignGraph, context: DesignContext) -> RuleResult:
        """Apply the matching rule and report its additions."""


def _add_component(
    graph: DesignGraph, node_id: str, node_type: str, name: str
) -> None:
    """Add one generated component and attach it to the gearbox."""
    graph.add_node(
        node_id,
        node_type,
        name,
        source="graph_rule",
        status="provisional",
        geometry_type=node_type.lower(),
    )
    graph.add_edge("gearbox", node_id, "contains")


class CreateGearboxSkeletonRule(DesignRule):
    """Create the root product node."""

    rule_id = "R01_create_gearbox_skeleton"
    description = "Create the gearbox product root."

    def matches(self, graph: DesignGraph, context: DesignContext) -> bool:
        """Match when the requirement task exists and the gearbox does not."""
        return graph.has_node("design_task") and not graph.has_node("gearbox")

    def apply(self, graph: DesignGraph, context: DesignContext) -> RuleResult:
        """Create the gearbox and attach it to the design task."""
        graph.add_node(
            "gearbox",
            "Gearbox",
            "single_stage_spur_gearbox",
            source="graph_rule",
            status="topology_in_progress",
        )
        graph.add_edge("design_task", "gearbox", "contains")
        return RuleResult(self.rule_id, True, ("gearbox",), self.description)


class AddSingleStageParallelShaftRule(DesignRule):
    """Add exactly one input and output shaft."""

    rule_id = "R02_add_single_stage_parallel_shafts"
    description = "Add parallel input and output shafts."

    def matches(self, graph: DesignGraph, context: DesignContext) -> bool:
        """Match after the gearbox exists and before either shaft exists."""
        return graph.has_node("gearbox") and not graph.has_node("input_shaft")

    def apply(self, graph: DesignGraph, context: DesignContext) -> RuleResult:
        """Create both shaft nodes and their parallel relation."""
        _add_component(graph, "input_shaft", "InputShaft", "input_shaft")
        _add_component(graph, "output_shaft", "OutputShaft", "output_shaft")
        graph.add_edge("input_shaft", "output_shaft", "parallel_to")
        return RuleResult(
            self.rule_id, True, ("input_shaft", "output_shaft"), self.description
        )


class AddGearPairRule(DesignRule):
    """Add a pinion, wheel, and one external gear mesh."""

    rule_id = "R03_add_gear_pair"
    description = "Add one external spur-gear pair and mesh."

    def matches(self, graph: DesignGraph, context: DesignContext) -> bool:
        """Match after shafts exist and before a pinion exists."""
        return graph.has_node("input_shaft") and not graph.has_node("pinion")

    def apply(self, graph: DesignGraph, context: DesignContext) -> RuleResult:
        """Create the gear pair and mesh connectivity."""
        _add_component(graph, "pinion", "Pinion", "pinion")
        _add_component(graph, "gear_wheel", "GearWheel", "gear_wheel")
        _add_component(graph, "gear_mesh", "GearMesh", "external_spur_mesh")
        graph.add_edge("pinion", "gear_wheel", "meshes_with")
        graph.add_edge("pinion", "gear_mesh", "contained_in")
        graph.add_edge("gear_wheel", "gear_mesh", "contained_in")
        return RuleResult(
            self.rule_id,
            True,
            ("pinion", "gear_wheel", "gear_mesh"),
            self.description,
        )


class AttachPinionRule(DesignRule):
    """Mount the pinion integrally on the input shaft."""

    rule_id = "R04_attach_pinion"
    description = "Attach pinion to input shaft."

    def matches(self, graph: DesignGraph, context: DesignContext) -> bool:
        """Match until the pinion has an integral relation."""
        return graph.has_node("pinion") and not graph.edges_by_type("integral_with")

    def apply(self, graph: DesignGraph, context: DesignContext) -> RuleResult:
        """Add both mounting and integral-manufacture semantics."""
        graph.add_edge("pinion", "input_shaft", "mounted_on")
        graph.add_edge("pinion", "input_shaft", "integral_with")
        return RuleResult(self.rule_id, True, message=self.description)


class AttachOutputGearRule(DesignRule):
    """Mount the gear wheel on the output shaft."""

    rule_id = "R05_attach_output_gear"
    description = "Attach gear wheel to output shaft."

    def matches(self, graph: DesignGraph, context: DesignContext) -> bool:
        """Match after the wheel exists and before its mounting edge."""
        mounted = graph.edges_by_type("mounted_on")
        return graph.has_node("gear_wheel") and not any(
            edge["source"] == "gear_wheel" for edge in mounted
        )

    def apply(self, graph: DesignGraph, context: DesignContext) -> RuleResult:
        """Mount the wheel on the output shaft."""
        graph.add_edge("gear_wheel", "output_shaft", "mounted_on")
        return RuleResult(self.rule_id, True, message=self.description)


class AddInputBearingPairRule(DesignRule):
    """Add two simplified input-shaft bearings."""

    rule_id = "R06_add_input_bearings"
    description = "Add left and right input bearings."

    def matches(self, graph: DesignGraph, context: DesignContext) -> bool:
        """Match until two input-bearing nodes have been created."""
        return graph.has_node("input_shaft") and not graph.has_node(
            "input_bearing_left"
        )

    def apply(self, graph: DesignGraph, context: DesignContext) -> RuleResult:
        """Create and connect the input-bearing pair."""
        ids = ("input_bearing_left", "input_bearing_right")
        for node_id in ids:
            _add_component(graph, node_id, "Bearing", node_id)
            graph.add_edge(node_id, "input_shaft", "supports")
        return RuleResult(self.rule_id, True, ids, self.description)


class AddOutputBearingPairRule(DesignRule):
    """Add two simplified output-shaft bearings."""

    rule_id = "R07_add_output_bearings"
    description = "Add left and right output bearings."

    def matches(self, graph: DesignGraph, context: DesignContext) -> bool:
        """Match until two output-bearing nodes have been created."""
        return graph.has_node("output_shaft") and not graph.has_node(
            "output_bearing_left"
        )

    def apply(self, graph: DesignGraph, context: DesignContext) -> RuleResult:
        """Create and connect the output-bearing pair."""
        ids = ("output_bearing_left", "output_bearing_right")
        for node_id in ids:
            _add_component(graph, node_id, "Bearing", node_id)
            graph.add_edge(node_id, "output_shaft", "supports")
        return RuleResult(self.rule_id, True, ids, self.description)


class AddOutputKeyRule(DesignRule):
    """Add the requested output-wheel parallel key."""

    rule_id = "R08_add_output_key"
    description = "Add a provisional key for the output gear."

    def matches(self, graph: DesignGraph, context: DesignContext) -> bool:
        """Match after the output wheel exists and before the key exists."""
        return graph.has_node("gear_wheel") and not graph.has_node("output_key")

    def apply(self, graph: DesignGraph, context: DesignContext) -> RuleResult:
        """Create the key and connect it to wheel and shaft."""
        _add_component(graph, "output_key", "Key", "output_key")
        graph.add_edge("output_key", "gear_wheel", "keyed_to")
        graph.add_edge("output_key", "output_shaft", "mounted_on")
        return RuleResult(self.rule_id, True, ("output_key",), self.description)


class AddHousingRule(DesignRule):
    """Add a simplified lower housing and removable cover."""

    rule_id = "R09_add_housing"
    description = "Add lower housing and housing cover."

    def matches(self, graph: DesignGraph, context: DesignContext) -> bool:
        """Match after bearings exist and before housing exists."""
        return graph.has_node("output_bearing_right") and not graph.has_node(
            "housing_lower"
        )

    def apply(self, graph: DesignGraph, context: DesignContext) -> RuleResult:
        """Create both enclosure components and containment relations."""
        _add_component(graph, "housing_lower", "Housing", "housing_lower")
        _add_component(graph, "housing_cover", "HousingCover", "housing_cover")
        enclosed = [
            "input_shaft",
            "output_shaft",
            "pinion",
            "gear_wheel",
            "input_bearing_left",
            "input_bearing_right",
            "output_bearing_left",
            "output_bearing_right",
        ]
        for node in enclosed:
            graph.add_edge(node, "housing_lower", "contained_in")
        return RuleResult(
            self.rule_id,
            True,
            ("housing_lower", "housing_cover"),
            self.description,
        )


class FinalizeTopologyRule(DesignRule):
    """Close the topology after every required component exists."""

    rule_id = "R10_finalize_topology"
    description = "Add the power path and mark topology complete."

    def matches(self, graph: DesignGraph, context: DesignContext) -> bool:
        """Match once all mandatory component instances exist."""
        required = [
            "gearbox",
            "input_shaft",
            "output_shaft",
            "pinion",
            "gear_wheel",
            "gear_mesh",
            "input_bearing_left",
            "input_bearing_right",
            "output_bearing_left",
            "output_bearing_right",
            "output_key",
            "housing_lower",
            "housing_cover",
        ]
        return not context.topology_complete and all(graph.has_node(n) for n in required)

    def apply(self, graph: DesignGraph, context: DesignContext) -> RuleResult:
        """Create an explicit input-to-output power path and finalize."""
        path = ["input_shaft", "pinion", "gear_wheel", "output_shaft"]
        for source, target in zip(path, path[1:]):
            graph.add_edge(source, target, "transmits_power_to")
        graph.update_node("gearbox", status="topology_complete")
        context.topology_complete = True
        return RuleResult(self.rule_id, True, message=self.description)


DEFAULT_RULES: tuple[DesignRule, ...] = (
    CreateGearboxSkeletonRule(),
    AddSingleStageParallelShaftRule(),
    AddGearPairRule(),
    AttachPinionRule(),
    AttachOutputGearRule(),
    AddInputBearingPairRule(),
    AddOutputBearingPairRule(),
    AddOutputKeyRule(),
    AddHousingRule(),
    FinalizeTopologyRule(),
)


class GraphGrammarEngine:
    """Apply the fixed MVP rules, with a hard execution limit."""

    def __init__(
        self, rules: tuple[DesignRule, ...] = DEFAULT_RULES, max_executions: int = 20
    ) -> None:
        """Configure fixed-order rules and an infinite-loop guard."""
        if max_executions < len(rules):
            raise ValueError("max_executions must allow every fixed rule to run")
        self.rules = rules
        self.max_executions = max_executions

    def run(
        self, requirement_graph: DesignGraph, requirement: GearboxRequirement
    ) -> tuple[DesignGraph, list[RuleResult]]:
        """Expand a copied requirement graph into the product topology."""
        graph = requirement_graph.copy()
        context = DesignContext(requirement=requirement)
        results: list[RuleResult] = []
        executions = 0
        while not context.topology_complete:
            progressed = False
            for rule in self.rules:
                if rule.rule_id in context.applied_rule_ids:
                    continue
                if rule.matches(graph, context):
                    results.append(rule.apply(graph, context))
                    context.applied_rule_ids.append(rule.rule_id)
                    executions += 1
                    progressed = True
                    if executions >= self.max_executions or context.topology_complete:
                        break
            if executions >= self.max_executions and not context.topology_complete:
                raise RuntimeError("graph grammar exceeded its execution limit")
            if not progressed and not context.topology_complete:
                raise RuntimeError("graph grammar cannot make further progress")
        return graph, results


def apply_graph_grammar(
    requirement_graph: DesignGraph, requirement: GearboxRequirement
) -> tuple[DesignGraph, list[RuleResult]]:
    """Apply the standard fixed rule sequence to a requirement graph."""
    return GraphGrammarEngine().run(requirement_graph, requirement)
