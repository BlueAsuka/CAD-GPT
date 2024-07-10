# AIDEA
Computer-Aided Design (CAD) with GPT, a future toward AI-aided Design (AAD) 

 ## Introduction

This is a repo for an experimental project that uses GPT to generate CAD models. It is not a single end-to-end model generation, but try to varify whether GPT can be used to generate small system consists of several components based on human's design requriements. In addition, this system can be later checked and validated by human operators before entering to the manufacturing state. 

The main idea is that apply GPT to generate a domain specific language (DSL) to represent the CAD models, and then use some graphic software or packages to generate the CAD models based on the generated DSL. In short, it generates the logic of generation instead of generating the final result directly. Similar idea can be found in the work of [3D-GPT](https://arxiv.org/abs/2310.12945), which apply GPT to generate a large-scale of 3D landscape with [Blender](https://www.blender.org/). By this method, human and the AI can together maintenance a same system based on the common domain specific language (DSL), therefore, the final results can be more controllable and be further customized by human.

The core idea is **Generate the logic of generation, rather generate the result directly.**

## System Framework
![](assets/CAD-GPT-workflow.jpg)
![](assets/GPT4CAD.png)

The domain specific language and the graphic package in this project is [OpenSCAD](https://openscad.org/), which is a free CAD software that use object scripting (formal language programming) to generate 3D models. Thus, it is a good option for this project. Also, for convienience, an OpenSCAD library on Thingiverese [gear.scad](https://www.thingiverse.com/thing:636119) is also included in this project, which is placed in the folder `openscad`.

## Requirement

OpenSCAD
Python >=3.9
OpenAI API Key 

## Some Examples
