include <gears.scad>
translate([0,0,0]) rotate([0,0,0])
gear_herringbone(m=2, z=20, h=25, w=20, w_helix=20);
translate([60,0,0]) rotate([0,0,360/(40*2)])
gear_herringbone(m=2, z=40, h=16, w=20, w_helix=-20);