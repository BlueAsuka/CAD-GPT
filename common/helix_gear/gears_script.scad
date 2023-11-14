include <gears.scad>

// Gear 1
translate([0, 0, 0]) rotate([0, 0, 360 / (20 * 2)]) gear_helix(m = 2, z = 20, x = 0, h = 20, w = 20, w_helix = 30);

// Gear 2
translate([50, 0, 0]) rotate([0, 0, 360 / (30 * 2)]) gear_helix(m = 2, z = 30, x = 0, h = 15, w = 20, w_helix = -30);
