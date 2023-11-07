// gears.scad
// library for parametric involute gears 
// Author: Rudolf Huttary, Berlin 
// last update: June 2016

iterations = 150; // increase for enhanced resolution beware: large numbers will take lots of time!
verbose = true;   // set to false if no console output is desired

// help();  // display module prototypes
// default values
// z = 10; // teeth - beware: large numbers may take lots of time!
// m = 1;  // modulus
// x = 0;  // profile shift
// h = 4;  // face_width	respectively axial height
// w = 20; // profile angle
// clearance  // assymmetry of tool to clear tooth head and foot
//    = 0.1; // for external splines
//    = -.1  // for internal splines 
// w_bevel = 45; // axial pitch angle
// w_helix = 45; // radial pitch angle 

// use this prototype:
// gear(m = modulus, z = Z, x = profile_shift, w = alpha, h = face_width);

//====  external splines with default values ===
// gear();  
// gear_helix(); 
// gear_herringbone(); 
// gear_bevel(); 

//====  internal splines with default values ===
// Gear();  
// Gear_helix(); 
// Gear_herringbone(); 
// Gear_bevel(); 
// 

//====  internal splines - usage and more examples ===
// gear(z = 25, m = 1, x = -.5, h = 4); 
// gear_bevel(z = 26, m = 1, x = .5, h = 3, w_bevel = 45, w_helix = -45); 
// gear_helix(z = 16, m = 0.5, h = 4, w_helix = -20, clearance = 0.1); 
//  gear_herringbone(z = 16, m = 0.5, h = 4, w_helix = -45, clearance = 0.1); // twist independent from height
// gear_herringbone(z = 16, m = 0.5, h = 4, w_abs = -20, clearance = 0.1);  // twist absolute


//====  external splines - usage and more examples ===
// D ist calculated automatically, but can also be specified
//
// Gear(z = 10, m = 1.1, x = 0, h = 2, w = 20,  D=18, clearance = -0.2); 
// gear(z = 10, m = 1, x = .5, h = 4, w = 20, clearance = 0.2); 

// Gear_herringbone(z = 40, m = 1, h = 4, w_helix = 45, clearance = -0.2, D = 49); 
// gear_herringbone(z = 40, m = 1, h = 4, w_helix = 45, clearance = 0.2); 

// Gear_helix(z = 20, m=1.3, h = 15, w_helix = 45, clearance = -0.2); 
// gear_helix(z = 20, m=1.3, h = 15, w_helix = 45, clearance = 0.2); 


// ====  grouped examples ===
//	di = 18; //axial displacement
//	translate([di, di])   Gear(z = 25, D=32); 
//	translate([-di, di])  Gear_helix(z = 25, D=32); 
//	translate([-di, -di]) Gear_herringbone(z = 25, D=32); 
//	translate([di, -di])  Gear_bevel(z = 25, D=32); 
	
//	di = 8; //axial displacement
//	translate([di, di])   gear(); 
//	translate([-di, di])  gear_helix(); 
//	translate([-di, -di]) gear_herringbone(); 
//	translate([di, -di])  gear_bevel(); 

// profile shift examples
//	di = 9.5; //axial displacement
//	gear(z = 20, x = -.5); 
//	translate([0, di+3]) rotate([0, 0, 0]) gear(z = 7, x = 0, clearance = .2); 
//	translate([di+3.4, 0]) rotate([0, 0, 0]) gear(z = 6, x = .25); 
//	translate([0, -di-3]) rotate([0, 0, 36])   gear(z = 5, x = .5); 
//	translate([-di-3.675, 0]) rotate([0, 0, 22.5]) gear(z = 8, x = -.25); 
 

// tooth cutting principle - dumping frames for video
//	s = PI/6; 
//	T= $t*360; 
//  U = 10*PI; 
//  difference()
//  {
//    circle(6);  // workpiece
//    for(i=[0:s:T])
//      rotate([0, 0, -i])
//      translate([-i/360*U, 0, 0])
//      Rack();  // Tool
//    }
//	rotate([0, 0, -T])
//	translate([-T/360*U, 0, 0])
//	color("red")
//  Rack();  // Tool




// === modules for internal splines
module help_gears()
{
helpstr = 
"gears library - Rudolf Huttay \n
  iterations = 150;\n
  verbose = true;\n
  help();\n
  help_gears();\n 
  gear(m = 1, z = 10, x = 0, h = 4, w = 20, clearance = 0, center = true);\n
  gear_helix(m = 1, z = 10, x = 0, h = 4, w = 20, w_helix = 45, w_abs = 0, clearance = 0, center = true, verbose = true, slices = undef);\n
  gear_herringbone(m = 1, z = 10, x = 0, h = 4, w = 20, w_helix = 45, w_abs = 0, clearance = 0, center = true, slices = undef);\n
  gear_bevel(m = 1, z = 10, x = 0, h = 4, w = 20, w_bevel = 45, w_helix = 45, w_abs = 0, clearance = 0, center = true);\n
  gear_info(m = 1, z = 10, x = 0, h = 0, w = 20, w_bevel = 0, w_helix = 0, w_abs=0, clearance = 0, center=true);\n
annular-toothed;\n
  Gear(m = 1, z = 10, x = 0, h = 4, w = 20, D = 0, clearance = -.1, center = true);\n
  Gear_herringbone(m = 1, z = 10, x = 0, h = 4, w = 20, w_helix = 45, w_abs = 0, D = 0, clearance = -.1, center = true);\n
  Gear_helix(m = 1, z = 10, x = 0, h = 4, w = 20, w_helix = 45, w_abs=0, D = 0, clearance = -.1, center = true);\n
  Gear_bevel(m = 1, z = 10, x = 0, h = 4, w = 20, w_bevel = 45, w_helix = 0, w_abs = 0, D = 0, clearance = 0, center = true);\n
2D primitives\n
  gear2D(m = 1, z = 10, x = 0, w = 20, clearance = 0);\n
  Rack(m = 1, z = 10, x = 0, w = 20, clearance = 0);\n
  ";
 echo(helpstr); 
}
module help() help_gears(); 
module Gear(m = 1, z = 10, x = 0, h = 4, w = 20, D = 0, clearance = 0, center = true) 
{
   D_= D==0 ? m*(z+x+4):D; 
   difference()
   {
		cylinder(r = D_/2, h = h, center = center);
		gear(m, z, x, h+1, w, center = center, clearance = clearance); 
	}
  if(verbose) echo(str("Ring (D) = ", D_)); 
}

module Gear_herringbone(m = 1, z = 10, x = 0, h = 4, w = 20, w_helix = 45, w_abs = 0, D = 0, clearance = 0, center = true) 
{
   D_= D==0 ? m*(z+x+4):D; 
   difference()
   {
		cylinder(r = D_/2, h = h, center = center); // CSG!
    translate([0, 0, -.001]) 
		gear_herringbone(m, z, x, h+.01, w, w_helix, w_abs, clearance = clearance, center = center); 
	}
  if(verbose) echo(str("Ring (D) = ", D_)); 
}

module Gear_helix(m = 1, z = 10, x = 0, h = 4, w = 20, w_helix = 45, w_abs=0, D = 0, clearance = 0, center = true) 
{
   D_= D==0 ? m*(z+x+4):D; 
   difference()
   {
		cylinder(r = D_/2, h = h-.01, center = center); // CSG!
		gear_helix(m, z, x, h, w, w_helix, w_abs, clearance, center); 
	}
  if(verbose) echo(str("Ring (D) = ", D_)); 
}

module Gear_bevel(m = 1, z = 10, x = 0, h = 4, w = 20, w_bevel = 45, w_helix = 0, w_abs = 0, D = 0, clearance = 0, center = true)
{
   D_= D==0 ? m*(z+x+4):D; 
   rotate([0, 180, 0])
   difference()
   {
		cylinder(r = D_/2, h = h-.01, center = center); // CSG!
		gear_bevel(m, z, x, h, w, w_bevel, w_helix, w_abs, clearance = clearance, center = center); 
	}
  if(verbose) echo(str("Ring (D) = ", D_)); 
}


// === modules for external splines
module gear_herringbone(m = 1, z = 10, x = 0, h = 4, w = 20, w_helix = 45, w_abs = 0, clearance = 0, center = true, slices = undef)
{
  gear_info("herringbone", m, z, x, h, w, undef, w_abs==0?w_helix:undef, w_abs==0?undef:w_abs, clearance, center);
  translate([0, 0, center?0:h/2])
   for(i=[0, 1])
   mirror([0,0,i])
   gear_helix(m, z, x, h/2, w, w_helix, w_abs, center = false, clearance = clearance, center = false, verbose = false, slices = slices); 
}

module gear_helix(m = 1, z = 10, x = 0, h = 4, w = 20, w_helix = 45, w_abs = 0, clearance = 0, center = true, verbose = true, slices=undef)
{
  if(verbose)
    gear_info("helix", m, z, x, h, w, undef, w_abs==0?w_helix:undef, w_abs==0?undef:w_abs, clearance, center);
	r_wk = m*z/2;
  tw = w_abs==0?h/tan(90-w_helix)/PI*180/r_wk:w_abs;
  sl = slices!=undef?slices:abs(tw)>0?ceil(2*h):1; 
	linear_extrude(height = h, center = center, twist = tw, slices = sl, convexity = z)
   gear2D(m, z, x, w, clearance); 
}

module gear_bevel(m = 1, z = 10, x = 0, h = 4, w = 20, w_bevel = 45, w_helix = 0, w_abs = 0, clearance = 0, center = true)
{
  gear_info("bevel", m, z, x, h, w, w_bevel, w_abs==0?w_helix:undef, w_abs==0?undef:w_abs, clearance, center);
	r_wk = m*z/2 + x; 
   sc = (r_wk-tan(w_bevel)*h)/r_wk; 
  tw = w_abs==0?h/tan(90-w_helix)/PI*180/r_wk:w_abs;
  sl = abs(tw)>0?ceil(2*h):1; 
	linear_extrude(height = h, center = center, twist = tw, scale = [sc, sc], slices = sl, convexity = z)
   gear2D(m, z, x, w, clearance); 
}

module gear(m = 1, z = 10, x = 0, h = 4, w = 20, clearance = 0, center = true)
{
  gear_info("spur", m, z, x, h, w, undef, undef, undef, clearance, center); 
	linear_extrude(height = h, center = center, convexity = z)
    gear2D(m, z, x, w, clearance); 
}

module gear_info(type = "", m = 1, z = 10, x = 0, h = 0, w = 20, w_bevel = 0, w_helix = 0, w_abs=0, clearance = 0, center=true, D=undef)
{
  	r_wk = m*z/2 + x; 
   	dy = m;  
  	r_kk = r_wk + dy;   
  	r_fk = r_wk - dy;  
  	r_kkc = r_wk + dy *(1-clearance/2);   
  	r_fkc = r_wk - dy *(1+clearance/2);  
  if(verbose) 
  {
   echo(str ("\n")); 
   echo(str (type, " gear")); 
   echo(str ("modulus (m) = ", m)); 
   echo(str ("teeth (z) = ", z)); 
   echo(str ("profile angle (w) = ", w, "°")); 
   echo(str ("pitch (d) = ", 2*r_wk)); 
   echo(str ("d_outer = ", 2*r_kk, "mm")); 
   echo(str ("d_inner = ", 2*r_fk, "mm")); 
   echo(str ("height (h) = ", h, "mm")); 
   echo(str ("clearance factor = ", clearance)); 
   echo(str ("d_outer_cleared = ", 2*r_kkc, "mm")); 
   echo(str ("d_inner_cleared = ", 2*r_fkc, "mm")); 
   echo(str ("helix angle (w_helix) = ", w_helix, "°")); 
   echo(str ("absolute angle (w_abs) = ", w_abs, "°")); 
   echo(str ("bevel angle (w_bevel) = ", w_bevel, "°")); 
   echo(str ("center  = ", center)); 
  }
}

// === from here 2D stuff == 
module gear2D(m = 1, z = 10, x = 0, w = 20, clearance = 0)
{
  	r_wk = m*z/2 + x; 
    U = m*z*PI; 
   	dy = m;  
  	r_fkc = r_wk + 2*dy *(1-clearance/2);  
  s = 360/iterations; 
  difference()
  {
    circle(r_fkc, $fn=300);  // workpiece
    for(i=[0:s:360])
      rotate([0, 0, -i])
      translate([-i/360*U, 0, 0])
      Rack(m, z, x, w, clearance);  // Tool
  }
}

module Rack(m = 2, z = 10, x = 0, w = 20, clearance = 0)
{
  polygon(rack(m, z, x, w, clearance)); 
}

function rack(m = 2, z = 10, x = 0, w = 20, clearance = 0) = 
  let (dx = 2*tan(w)) 
  let (c = clearance/m) 
  let (o = dx/2-PI/4) 
  let (r = z/2 + x + 1) 
  let(X=[c, PI/2-dx-c, PI/2-c, PI-dx+c]) 
  let(Y=[r-c, r-c, r-2-c, r-2-c])
  m*concat([[-PI+o, r+5]], 
           [for(i=[-1:z], j=[0:3]) [o+i*PI+X[j], Y[j]]], 
           [[o+PI*(z+1)+c, r-c], [o+PI*(z+1)+c, r+5]]); 

