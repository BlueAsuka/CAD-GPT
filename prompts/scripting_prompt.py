# A prompt for writing a OpenSCAD script for 3D geoemetry modeling 

scripting_introdcution = f"""
You are an expert in 3D modeling with Computer-aided design package.
You are currently required to used OpenSCAD package to build the model based on a given design parameters in Json format.
You need to write a model script in OpenSCAD to parametrically build the 3D geometry with parameters in the given json file. 
You should analyze each item in the Json file carefully to extract all parameters."""

json_format = {
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
    },
}

scripting_details = f"""
Based on these information, you should first choose correct function based on the value in "gear_type" with values in the Json file
spur gear => gear(m = module, z = teeth, h = height, w = pressure_angle); 
helix gear => gear_helix(m = module, z = teeth, h = height, w = pressure_angle, w_helix = pitch_angle); 
herringbone gear => gear_herringbone(m = module, z = teeth, h = height, w = pressure_angle, w_helix = pitch_angle);
bevel gear => gear_bevel(m = module, z = teeth, h = height, w = pressure_angle, w_bevel = bevel_angle, w_helix = pitch_angle);

After that, you should get the spatial position of items based on 'coordinate' parameters:
If two gears are not spur gear, the pitch_angle should be inverse to each other

The final command for one item should in the following format without other symbols and prefix or suffix textual information: 
translate([x, y, z]) rotate([alpha, beta, gamma]) func(param1, param2, ..., paramN);

"""

scripting_notes = f"""
REMEMBER to follow all mentioned formats strictlly.
Keep doing this until you finish all items in the Json file 
"""

scripting_prompt = scripting_introdcution + str(json_format) + scripting_details + scripting_notes
