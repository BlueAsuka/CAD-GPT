# CadQuery Gearbox Agent Architecture

## Why this is a fixed pipeline

`gearen` does not use LangChain, LangGraph, CrewAI, AutoGen, or a general
workflow engine. The supported problem is narrow, and the order of engineering
operations matters. A fixed pipeline makes every transition visible, keeps
mechanical calculations reproducible, and makes a failed stage easy to rerun in
a debugger.

The word “Agent” here means that one command takes a requirement through an
inspectable design workflow. It does not mean that an LLM is free to choose the
next action.

## Pipeline stages

`GearboxDesignPipeline.run()` is the main reading path.

1. `parse_requirement`: regular expressions extract the supported Chinese
   phrases and preserve provenance.
2. `validate_requirement`: blocking scope conflicts stop the run; centralized
   assumptions and unresolved details are recorded.
3. `build_graph`: a Requirement Graph connects the task to structured fields.
4. `generate_topology`: ten fixed rules create the supported Product Graph.
5. `calculate_parameters`: pure functions derive speed and torque.
6. `search_candidates`: teeth, standard modules, and face widths are enumerated.
7. Candidate selection takes the first item in the transparent MVP ranking.
8. `solve_layout`: shafts, gears, bearings, key, and housing receive coordinates.
9. `generate_cad`: deterministic CadQuery builders produce parts and assembly.
10. `validate_design`: requirement, graph, parameter, layout, and geometry
    checks produce explicit statuses.
11. Reports and trace files are written before the stage becomes `complete`.

`need_user_input` is returned for blocking requirements. Exceptions are not
silently converted into engineering success.

## LLM boundary

The MVP needs no API key. `RuleBasedRequirementParser` is the active parser.
`LLMRequirementParser` is only an interface boundary. If it is implemented,
its output must be JSON validated by `GearboxRequirement`.

An LLM may help interpret language, but it must not:

- calculate teeth, forces, torque, centre distance, or shaft diameter;
- choose the next pipeline stage;
- emit executable CadQuery code;
- declare strength, life, certification, or manufacturing suitability.

Those responsibilities stay in deterministic Python and explicit validation.

## Data flow by file

```text
cli.py
  -> pipeline.py
     -> requirement_parser.py -> models.py
     -> requirement_validator.py
     -> design_graph.py -> grammar_rules.py
     -> calculations.py -> candidate_search.py
     -> layout.py
     -> cad/{gear,shaft,bearing,key,housing,assembly}.py
     -> validation.py -> reporting.py
     -> outputs/<run_id>/
```

No module imports from `paper_code/`. The original paper implementation is a
separate reference and remains runnable by following `paper_code/README.md`.

## Debugging one stage

1. Run `python -m gearen.cli design --file <path>`.
2. Open `trace/pipeline_trace.jsonl` and identify the last completed stage.
3. Inspect the matching directory:

   - parser/validator: `requirements/`;
   - graph rules: `graphs/` and `trace/grammar_trace.json`;
   - search: `synthesis/`;
   - layout: `layout/layout.json`;
   - CAD: `cad/`;
   - validation: `reports/validation_report.json`.

4. Reproduce the stage with its unit test. For CAD, start with
   `pytest tests/test_cad.py -vv`.
5. Use `validate <run_dir>` to rerun checks, or `regenerate-cad <run_dir>` to
   rebuild geometry without reparsing the original text.

The saved artifacts use UTF-8 JSON and stable component identifiers so they can
also be inspected with small standalone scripts.

