# CAP

CAP is a refactored continuation of the original CAD-GPT paper code illustrated in the following link:

[An Investigation on Utilizing Large Language Model for Industrial Computer-Aided Design Automation](https://www.sciencedirect.com/science/article/pii/S2212827124006656)

The project explores how large language models (LLMs) can support computer-aided design by generating a chain of verfiable and editable intermediate steps for engineering design. The workflow is designed to be human-readable and editable, rather than trying to generate the final geometry directly.

The original implementation for the paper is preserved in [`paper_code/`](paper_code/). New work in this repository focuses on restructuring that prototype into a cleaner agentic workflow and moving the CAD backend toward [CadQuery](https://github.com/CadQuery/cadquery), a Python-native parametric CAD library.

## Paper Background

The paper implementation used GPT to translate a human design requirement into intermediate CAD design logic, parameter descriptions, and OpenSCAD scripts. The central idea remains:

**Generate the logic of generation, rather than generate the result directly.**

Instead of treating an LLM as a black-box 3D model generator, the workflow asks the model to produce inspectable, editable, domain-specific CAD instructions. Human designers can then review, validate, modify, and rerun the generated logic.

## Repository Layout

```text
.
|-- agent.py              # Early refactored agent abstraction
|-- paper_code/           # Original paper implementation and reproduction materials
|   |-- README.md         # Detailed guide for the paper code
|   |-- notebooks/        # Jupyter notebooks for the original experiments
|   |-- docs/             # The paper of the code 
|   |-- prompts/          # Prompt templates used by the paper workflow
|   |-- common/           # OpenSCAD gear examples and generated artifacts
|   |-- config/           # Example configuration for the paper code
|   `-- assets/           # Workflow diagrams and result images
`-- LICENSE
```

## How to Read This Repository

If you are new to the project, start with the paper code:

1. Read [`paper_code/README.md`](paper_code/README.md) to understand the original CAD-GPT workflow. Also, read the paper to get to know more if interested in some details in the `paper_code/docs` folder.
2. Run or inspect the notebooks in [`paper_code/notebooks/`](paper_code/notebooks/) to see how requirements are converted into CAD parameters and OpenSCAD scripts.
3. Return to the root-level code to follow the refactoring effort toward a more modular agentic CAD system.
4. Run the code in the `paper_code` following the commands in the README.md file.
 
The `paper_code/` folder is intentionally kept as a reference implementation. It is the best entry point for understanding the paper, the motivation, and the original proof of concept.

## Refactoring Direction

The updated repository is intended to move from a notebook-centered OpenSCAD prototype toward a more maintainable system with:

- A clearer agentic workflow for planning, CAD code generation, tool execution, validation, and memory.
- A CadQuery backend for Python-native parametric CAD generation.
- Modular components that separate prompting, model calls, design reasoning, CAD construction, validation, and export.
- More inspectable intermediate artifacts so human designers can understand and revise the generated design logic.
- A foundation for supporting more complex assemblies beyond the original gear examples.

The current root-level `agent.py` is an early step in separating the agent loop from the original notebooks. The paper implementation should still be treated as the complete runnable baseline.

## Current Status

This repository is in transition. The original paper code is available under `paper_code/`, while the root-level project is being refactored around a more general agentic CAD workflow and a CadQuery-based backend.

Use `paper_code/` when you want to reproduce or understand the original research idea. Use the root of the repository when you want to follow or extend the updated implementation.

## Citation

If you use this repository for academic work, please cite the original paper linked above.

```
@article{deng2024investigation,
  title={An investigation on utilizing large language model for industrial computer-aided design automation},
  author={Deng, Haoxuan and Khan, Samir and Erkoyuncu, John Ahmet},
  journal={Procedia CIRP},
  volume={128},
  pages={221--226},
  year={2024},
  publisher={Elsevier}
}
```

## CadQuery Gearbox Design Agent

`paper_code/` remains the original paper implementation and reproduction
material. Follow [`paper_code/README.md`](paper_code/README.md) for its original
notebooks, configuration, dependencies, and run instructions. The new
`gearen/` package is an independent CadQuery experiment: it does not modify or
import private modules from `paper_code/`.

### Repository structure

```text
.
|-- paper_code/       # preserved original paper implementation
|-- requirements/     # default Chinese natural-language input
|-- gearen/           # deterministic design pipeline
|   |-- cad/          # CadQuery part and assembly builders
|   `-- data/         # standard modules and simplified bearing catalog
|-- tests/            # rule, graph, calculation, layout, CAD, and E2E tests
|-- docs/             # architecture and extension guides
|-- outputs/          # ignored per-run artifacts; .gitkeep is retained
`-- pyproject.toml
```

### Installation

Python 3.10 or newer is required. CadQuery includes a substantial OpenCascade
binary dependency, so an isolated environment is recommended.

```bash
python -m venv .venv
# Windows
.venv\Scripts\python -m pip install -e '.[test]'
# Linux/macOS
.venv/bin/python -m pip install -e '.[test]'
```

No LLM API key is required. `.env.example` only documents a possible future
structured-output parser integration.

### Run

```bash
python -m gearen.cli design
python -m gearen.cli design --file requirements/requirements_text.txt
python -m gearen.cli design --text '设计一个单级圆柱齿轮减速器，功率10kW，传动比3，输入转速1440rpm'
python -m gearen.cli inspect outputs/<run_id>
python -m gearen.cli validate outputs/<run_id>
python -m gearen.cli regenerate-cad outputs/<run_id>
```

The default command reads `requirements/requirements_text.txt`. Each design
uses a new sortable run ID and never overwrites another run.

### Explicit workflow

```mermaid
flowchart LR
  A[Natural-language requirement] --> B[Structured Requirement]
  B --> C[Requirement validation]
  C --> D[Requirement Graph]
  D --> E[Fixed graph grammar]
  E --> F[Product Graph]
  F --> G[Mechanical calculations]
  G --> H[Candidate enumeration]
  H --> I[Deterministic layout]
  I --> J[CadQuery parts and assembly]
  J --> K[Validation and reports]
```

The pipeline, not an LLM, controls this order. Formulas, candidate scoring,
layout, CAD, and validation are deterministic Python.

### Run artifacts

An `outputs/<run_id>/` directory contains:

- `input/`: an exact copy of requirement text;
- `requirements/`: structured values, provenance, assumptions, and review;
- `graphs/`: Requirement/Product Graph JSON and Product Graph GraphML;
- `synthesis/`: all ranked candidates and the selected provisional candidate;
- `layout/`: component origins, axes, envelopes, shafts, bearings, and key;
- `cad/`: individual STEP files, named assembly STEP, and merged STL;
- `reports/`: formulas, validation statuses, limitations, and summary;
- `trace/`: pipeline stage and graph-rule execution records.

### Current supported scope

- one-stage external spur cylindrical reduction;
- parallel input and output shafts;
- one pinion and one gear wheel;
- two simplified deep-groove bearings per shaft;
- a provisional output-wheel parallel key;
- a simplified split housing and deterministic CadQuery assembly;
- Chinese extraction for power, ratio, speed, calendar years, indoor/outdoor,
  temperature range, single stage, and cylindrical gear terms.

The default 10 kW, ratio 3, 1440 rpm example calculates 480 rpm output speed.
Calendar life is preserved as years; it is not silently changed into 87,600
operating hours.

### Current limitations and status meanings

The gear solids use outside-diameter discs and hubs. They are useful for
envelope and pipeline testing but are not exact involute teeth. Shaft sizing is
torsion-only. Bearings and keys are concept catalog selections. The MVP does
not claim ISO 6336, rated bearing life, tooth contact, complete assembly
process planning, FEA, thermal analysis, or certification.

Missing daily hours, annual working days, load spectrum, and shock level do not
stop concept synthesis. They remain unresolved, bearing-life and gear-strength
checks are `blocked`, and shaft/key/CAD fidelity checks are `provisional`.
Interactive preview is not produced in a headless CLI; use the generated STEP
or STL in an external viewer.

**This project generates concept-level parametric design results. They must not
be used directly for manufacturing, safety-critical systems, or industrial
certification.**

### Extend and debug

- [`docs/architecture.md`](docs/architecture.md) explains stage boundaries,
  data flow, the LLM boundary, and stage-level debugging.
- [`docs/design_graph.md`](docs/design_graph.md) documents nodes, edges, fixed
  rules, parameter enrichment, layout, and CAD conversion.
- [`docs/extending_the_agent.md`](docs/extending_the_agent.md) gives concrete
  steps for helical gears, two-stage units, exact involutes, ISO checks, graph
  rules, and new CAD parts.

### Test

```bash
python -m pytest
```

Tests do not call an external LLM. They include the default end-to-end run,
actual CadQuery shape and STEP generation, validation statuses, and a source
scan that prevents `gearen` from depending on `paper_code`.
