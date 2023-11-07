# A prompt for reasoning on converting the task into a set of instructions

reasoning_prompt = f"""
You are an expert in commanding and instructions construction. 
You are required to generate accurate descriptions for instructing an agent to use corresponding functions based on a set of parameters.

EXAMPLE:
You receive a set of parameters for external spur gear system designing in the format of list [z, m, h]
Where z is the number of teeth, m is the modulus number of the gear, h is the axial height of the gear

You should give instruction based on this list 
1. 
"""