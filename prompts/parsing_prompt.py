# A prompt for parsing a json format file for list parameters of parts 

import os
import json


parsing_introduction = f"""
You are an expert in commanding and instructions construction in JSON files. 
You receive a textural description of a set of parameters for external spur gear system designing.
You should analysis and detect parameters writen in the textual description accurately.
You should fill the parse a json file by replacing '' in each item with parameters in the given description.
"""

with open(os.path.join(os.path.dirname(__file__), "parameters_format.json"), "r") as f:
    json_format = json.load(f)
    
parsing_notes = f"""
REMEMBER to parse all items in given descriptions
For 'gear_type', ONLY use following keywords: 'spur', 'helix' 'herringbone', and 'bevel'.
For 'source', ONLY 'driven' and 'driving' based on textual descriptions.
For all parameters in 'coordinate' in the json file should be represented in numerical value, not in string format.
For angular parameters in 'coordinate': alpha, bete, and gamma are all set to 0 in default.
For all spur gears, the 'helix_angle' and 'pitch_angle' should be 0.
For spur, helix and herringbone gears, the 'pitch_angle' should be 0.
"""

parsing_prompt = parsing_introduction + str(json_format) + parsing_notes


if __name__ == '__main__':
    print(os.path.join(os.path.dirname(__file__), "parameters_format.json"))
    print(json_format)
