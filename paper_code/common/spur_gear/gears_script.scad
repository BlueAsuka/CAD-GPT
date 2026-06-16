include <gears.scad>
translate([0,0,0]) rotate([0,0,0])
gear(m=2.5, z=20, h=18, w=20);

translate([100,0,0]) rotate([0,0,(360/(60*2))])
gear(m=2.5, z=60, h=27, w=20);