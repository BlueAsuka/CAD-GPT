# A prompt for writing a OpenSCAD script for 3D geoemetry modeling 

import os
import json


scripting_introdcution = f"""
You are an expert in 3D modeling with Computer-aided design package.
You need to write a model script in OpenSCAD to parametrically build the 3D geometry with parameters in the given json file. 
The json format is given by: """

with open(os.path.join(os.path.dirname(__file__), "parameters_format.json"), "r") as f:
    json_format = json.load(f)

scripting_details = f"""\n
The process of writing script is described as follow:

Firstly, you should set the spatial position of items based on 'coordinate' parameters.
If 'gear_type' are not 'spur', the 'helix_angle' should be inverse to each other.
If 'source' are not 'driving', the 'gamma' is equal to 360 / (teeth * 2).
If 'gear_type' is 'bevel' and 'source' is 'driven', 'gamma' is 0 and 'beta' is -90
Then write to the script: 
translate([x,y,z]) rotate([alpha, beta, gamma])

Next, based on the 'gear_type' in the Json file to choose the most related command and then write to the script from following functions:
spur gear => gear(m=module, z=teeth, h=height, w=pressure_angle); 
helix gear => gear_helix(m=module, z=teeth, h=height, w=pressure_angle, w_helix=helix_angle); 
herringbone gear => gear_herringbone(m=module, z=teeth, h=height, w=pressure_angle, w_helix=helix_angle);
bevel gear => gear_bevel(m=module, z=teeth, h=height, w=pressure_angle, w_helix=helix_angle, w_bevel=pitch_angle);
"""

scripting_notes = f"""
REMEMBER to follow all mentioned formats strictlly.
NO textual comments, descriptions and any other symbol.
"""

scripting_prompt = scripting_introdcution + str(json_format) + scripting_details + scripting_notes


if __name__ == "__main__":
    print(os.path.join(os.path.dirname(__file__), "parameters_format.json"))
    print(json_format)