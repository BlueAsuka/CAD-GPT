# A prompt for reasoning on converting the task into a set of instructions

parsing_introduction = f"""
You are an expert in commanding and instructions construction in JSON files. 
You receive a textural description of a set of parameters for external spur gear system designing.
You should analysis and detect parameters writen in the textual description accurately.
You are required to parse a json file in the provided format based on the description for formalization.
You should fill the provided json format by replacing '' in each item with parameters in the given description.
"""

parsing_format = {
    "gear 1":{
        "gear_type": '',
        "coordinate": {"x": '', "y": '', "z": '', 'alpha': '', 'beta': '', 'gamma': ''},
        "unit": '',
        "module": '',
        "teeth": '',
        "height": '',
        "pitch_d": '',
        "pitch_angle": '',
        "pressure_angle": ''
    }
}

parsing_notes = f"""
For 'gear_type', ONLY use following keywords: 'spur', 'helix' 'herringbone', and 'bevel'.
For all parameters in 'coordinate' in the json file should be represented in numerical value, not in string format.
For angular parameters in 'coordinate': alpha, bete, and gamma are all set to 0 in default.
For all spur gears, the 'pitch_angle' should be 0.
"""

parsing_prompt = parsing_introduction + str(parsing_format) + parsing_notes
