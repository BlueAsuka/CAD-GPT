# Requirement and Product Graphs

## Two graph roles

The Requirement Graph records what was requested, calculated, inferred, or left
unresolved. Its `DesignTask` node has `has_requirement` edges to one
`Requirement` node per structured field and additional unresolved nodes.

The Product Graph starts as a copy of that graph. Fixed graph rules then add the
supported gearbox component and connection topology. The original requirement
nodes remain, providing traceability from input to product.

The graph is not CAD. It contains only JSON-serializable values.

## Nodes

Every node has:

- `id`: stable identifier;
- `node_type` and `name`;
- serializable `attributes`;
- `source` and `status`;
- `geometry_type`;
- `geometry_parameters`.

Product node types include `Gearbox`, `InputShaft`, `OutputShaft`, `Pinion`,
`GearWheel`, `GearMesh`, `Bearing`, `Key`, `Housing`, and `HousingCover`.

Stable component IDs such as `pinion`, `output_bearing_left`, and
`housing_cover` are reused by layout, CAD, validation, and exported filenames.

## Edges

Connections use a small vocabulary:

- ownership: `contains`, `contained_in`;
- mechanical connection: `mounted_on`, `integral_with`, `keyed_to`;
- interaction: `meshes_with`, `supports`;
- spatial relation: `parallel_to`;
- functional flow: `transmits_power_to`;
- traceability: `has_requirement`.

`DesignGraph` wraps `networkx.MultiDiGraph`. Other modules use `add_node`,
`add_edge`, `nodes_by_type`, `edges_by_type`, `to_dict`, and export methods,
without manipulating NetworkX internals.

## Fixed graph grammar

The rules execute in this order:

1. create the gearbox root;
2. add one parallel input/output shaft pair;
3. add pinion, wheel, and mesh;
4. attach the pinion;
5. attach the output wheel;
6. add two input bearings;
7. add two output bearings;
8. add the output key;
9. add lower housing and cover;
10. add the power path and finalize.

Each rule checks for stable IDs before adding anything. The engine records each
application, never reapplies the same rule, has a maximum execution count, and
fails if no rule can make progress. This is intentionally not a general graph
rewriting language.

## From topology to geometry

The stages have separate responsibilities:

```text
graph grammar
  components + connections
        |
parameter calculation/search
  teeth + module + width + loads
        |
layout
  origins + axes + envelopes
        |
CadQuery builders
  deterministic solids + assembly
```

After candidate selection, calculated parameters are copied into the pinion,
wheel, and mesh nodes. Layout stays in `layout.json`; CadQuery objects are never
stored in either graph.

`product_graph.json` is best for inspection. `product_graph.graphml` is useful
for graph tools such as Gephi or yEd; nested fields are JSON-encoded strings
because GraphML attributes are scalar.

