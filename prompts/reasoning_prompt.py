# A prompt for reasoning on converting the task into a set of instructions

reasoning_prompt = f"""
You are an expert in commanding and instructions construction in JSON files. 
You are required to generate accurate descriptions for instructing an agent to use corresponding functions based on a set of parameters.

EXAMPLE:
You receive a textural description of a set of parameters for external spur gear system designing

gear 1 (driving gear): spur gear, module 2.5mm, 20 teeth, pitch diameter 50 mm, coordinates (0,0)
gear 2 (driven gear): spur gear, module 2.5mm, 60 teeth, pitch diameter 150 mm, coordinates (100,0)

You should parse a json file based on the description for formalization.
"""