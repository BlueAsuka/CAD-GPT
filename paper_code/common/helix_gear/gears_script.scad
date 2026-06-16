include <gears.scad>
translate([0,0,0]) rotate([0, 0, 0])
gear_helix(m=2.5, z=16, h=15, w=20, w_helix=20);

translate([50,0,0]) rotate([0, 0, 360 / (24 * 2)])
gear_helix(m=2.5, z=24, h=20, w=20, w_helix=-20);