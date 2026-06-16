include <gears.scad>
translate([0,0,0]) rotate([0, 0, 0])
gear_bevel(m=2, z=20, h=20, w=20, w_helix=0, w_bevel=45);

translate([40,0,40]) rotate([0, -90, 0])
gear_bevel(m=2, z=40, h=20, w=20, w_helix=0, w_bevel=45);