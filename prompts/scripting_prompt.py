# A prompt for writing a OpenSCAD script for 3D geoemetry modeling 

scripting_introdcution = f"""
You are an expert in 3D modeling with Computer-aided design package.
You need to write a model script in OpenSCAD to parametrically build the 3D geometry with parameters in the given json file. 
The json format is given by: """

json_format = {
    "gear 1":{
        "gear_type": '',
        "source": '',
        "coordinate": {"x": '', "y": '', "z": '', 'alpha': '', 'beta': '', 'gamma': ''},
        "unit": '',
        "module": '',
        "teeth": '',
        "height": '',
        "pitch_d": '',
        "pitch_angle": '',
        "pressure_angle": ''
    },
}

scripting_details = f"""\n
The process of writing script is described as follow:

Firstly, you should set the spatial position of items based on 'coordinate' parameters.
If 'gear_type' are not 'spur', the pitch_angle should be inverse to each other.
If the 'source' are not 'driving', the 'gamma' is equal to 360 / (teeth * 2), then write to the script: 
translate([x,y,z]) rotate([alpha, beta, gamma])

Next, based on the 'gear_type' in the Json file to choose the most related command and then write to the script from following functions:
spur gear => gear(m=module, z=teeth, h=height, w=pressure_angle); 
helix gear => gear_helix(m=module, z=teeth, h=height, w=pressure_angle, w_helix=pitch_angle); 
herringbone gear => gear_herringbone(m=module, z=teeth, h=height, w=pressure_angle, w_helix=pitch_angle);
bevel gear => gear_bevel(m=module, z=teeth, h=height, w=pressure_angle, w_helix=pitch_angle, w_bevel=bevel_angle);
"""

scripting_notes = f"""
REMEMBER to follow all mentioned formats strictlly.
NO textual comments, descriptions and any other symbol.
"""

scripting_prompt = scripting_introdcution + str(json_format) + scripting_details + scripting_notes
