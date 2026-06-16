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
