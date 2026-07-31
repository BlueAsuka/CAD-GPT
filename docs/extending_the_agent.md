# Extending the Gearbox Agent

Start by adding a failing test and keep new behavior outside `paper_code/`.
Extend the explicit pipeline only when the new deterministic stage has a clear
input and output.

## Add helical gears

1. Add helix angle and handedness fields to `GearboxRequirement` and a candidate
   model dedicated to helical gears.
2. Change validation so `helical` is accepted only when the implementation is
   complete; until then it must remain blocking.
3. Add normal/transverse module and pressure-angle formulas as pure functions.
4. Add an explicit helical gear-pair rule or parameterize the existing pair
   rule. Do not dynamically register rules.
5. Implement a `HelicalGearBackend` with deterministic geometry.
6. Add axial-force, opposite-hand mesh, layout, CAD, and export tests.
7. Document which ISO strength and contact checks are still missing.

## Add a two-stage reducer

1. Create a separate two-stage requirement/topology data path; do not weaken
   the single-stage cardinality checks.
2. Add an intermediate shaft, two meshes, and two gear pairs with stable IDs.
3. Enumerate ratio splits explicitly and rank them with a documented score.
4. Extend layout with two centre distances and interference envelopes.
5. Build the larger housing from both mesh envelopes.
6. Add stage-specific graph, power-path, ratio-product, layout, and CAD tests.
7. Only then allow `stage_count=2` in requirement validation.

## Add an exact involute backend

1. Keep `GearGeometryBackend` unchanged.
2. Implement `InvoluteGearBackend.build()` from a verified involute profile,
   root transition, addendum, dedendum, backlash, and tolerance definition.
3. State the adopted gear standard and profile-shift convention.
4. Compare pitch/base/outside/root diameters against reference cases.
5. Add section and mesh-quality tests before selecting it as the default.
6. Preserve `SimplifiedGearBackend` for fast envelope testing.

## Add ISO strength checks

1. Add explicit material, heat treatment, quality grade, load spectrum,
   reliability, and application factors to the data model.
2. Block the check when any mandatory factor is absent; never invent values.
3. Put each equation in a typed pure function with units and clause references.
4. Keep calculation inputs and intermediate factors in the report.
5. Validate against published standard examples that the project is permitted
   to reproduce.
6. Call the result an implemented subset until all stated clauses are covered.

## Add a graph rule

1. Give the component a stable node ID and one of the documented node types, or
   deliberately add a new node type to `design_graph.py`.
2. Implement one `DesignRule` with narrow `matches()` and idempotent `apply()`.
3. Insert it at the intended location in `DEFAULT_RULES`.
4. Increase the execution limit only if the rule count requires it.
5. Assert its node cardinality and connection edges in
   `tests/test_design_graph.py`.
6. Update `docs/design_graph.md` and validation.

## Add a CAD part

1. Create one builder in `gearen/cad/` that takes a typed, unit-documented
   parameter object and returns `cq.Workplane`.
2. Keep local geometry aligned to the X-axis convention.
3. Add a stable layout placement and Product Graph node/edges.
4. Add the stable name to `PART_ORDER`, assembly colors if useful, and exports.
5. Test a non-null shape, positive bounding box, individual STEP, assembly STEP,
   and obvious clearances.
6. Add validation wording that distinguishes simplified visual geometry from
   verified manufacturing geometry.

