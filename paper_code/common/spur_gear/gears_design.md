
The gear ratio indicates the relationship between the speeds, torques, and diameters of two gears in mesh
For a gear ratio of 3:1, the driven gear must have three times as many teeth as the driving gear, or the driving gear must have three times as small a diameter compared to the driven gear.

Here's how we can compute the parameters for the gears:

1
**Choose a standard module size**: The module of a gear is a measure of the gear tooth size which is equal to the pitch diameter divided by the number of teeth
The module (m) must be chosen such that the gears will have a whole number of teeth
The module size will also depend on factors like the power transmission requirements and space constraints
For simplicity, we can start with an arbitrary module size and adjust later if needed.

2
**Calculate teeth number for both gears**: Given the 3:1 gear ratio, if we assign the driving gear (smaller gear) Z1 teeth, the driven gear (larger gear) will have Z2 = 3 * Z1 teeth.

3
**Pitch diameters of both gears**: The pitch diameter (d) can be found using the formula d = m * Z, where Z is the number of teeth and m is the module.

   - For the driving gear:
     $$d1 = m * Z1$$

   - For the driven gear:
     $$d2 = m * Z2 = m * (3 * Z1) = 3 * d1$$

4
**Center distance between gears**: The sum of the radii of the gears must equal the center distance
Using the pitch diameters, this can be expressed as:

   $$d1 / 2 + d2 / 2 = Center Distance$$

   $$m * Z1 / 2 + m * 3 * Z1 / 2 = 100 mm$$

   $$m * Z1 * 2 = 100 mm$$

   $$m * Z1 = 100 mm$$

5
**Choosing Teeth Numbers**: Let's choose a small number of teeth for the driving gear Z1 to ensure the gears aren't too large
Common industrial practice allows for a pinion (smaller gear) to have as few as 18 teeth to avoid undercutting and excessive wear.

   Assuming Z1 = 18 (for the driving gear), and m * Z1 = 100 mm, we get:

   $$m = 100 mm / Z1$$
   $$m = 100 mm / 18$$
   $$m ≈ 5
56 mm$$

   As modules are typically standard sizes, we should choose a standard value that's close to our calculated one to ensure ready availability of gears
The neighboring standard module sizes are 5 and 6 mm
Let's choose m = 5 mm, which is slightly smaller than the computed value, to ensure our gears fit within the space constraints.

   Therefore, Z1 = 18 teeth and Z2 = 3 * Z1 = 54 teeth.

6
**Coordinates of the driven gear**: With the driving gear at the center (0,0), the driven gear will be located at a distance equal to the center distance
Since we changed the module to 5 mm, the actual center distance for standard module m = 5 mm would be:

   $$Center Distance = (m * Z1 / 2) + (m * Z2 / 2)$$
   $$Center Distance = (5 mm * 18 / 2) + (5 mm * 54 / 2)$$
   $$Center Distance = (45 mm) + (135 mm)$$
   $$Center Distance = 180 mm$$

   This is significantly larger than the initial 100 mm requirement
To meet the 100 mm requirement, a smaller module should be chosen or a smaller number of teeth for the driving gear, which would proportionally reduce the teeth on the driven gear and result in a smaller center distance.

   For a 100 mm center distance with a 3:1 gear ratio, we must go back and choose a small enough module to maintain proper sizing
Let's try with Z1 = 18 and a 100 mm center distance while maintaining the 3:1 ratio:

   - Gear 1: m * Z1 / 2 = 100 mm / 4 = 25 mm
   
   - Gear 2: (m * 3 * Z1) / 2 = 75 mm
   
   From Gear 1, we find that m * Z1 = 50 mm
   
   Plugging in Z1 = 18, we get m = 50 mm / 18 ≈ 2
78 mm
   
   We could round this to a standard module size
The choice could be m = 2
5 mm or m = 3 mm, depending on other design considerations
If we select m = 2
5 mm:

   Z1 = 18 teeth
   Z2 = 54 teeth
   
   - Gear 1: m * Z1 = 2
5 mm * 18 = 45 mm
   - Gear 2: 3 * m * Z1 = 3 * 45 mm = 135 mm
   
   The actual center distance will be:
   
   $$ (45 mm / 2) + (135 mm / 2) = 90 mm $$
   
   This still isn't 100 mm, which means we must further adjust our variables
Since the desired center distance is very specific and directly impacts gear size, we might need to choose a non-standard module or alter the tooth count again, ensuring we retain an integer number of teeth for each gear and maintain the 3:1 ratio.

   For a precise match to the required 100 mm center distance, let's adjust Z1:
   
   Center Distance = m * (Z1 + 3 * Z1) / 2 = 100 mm
                   = m * (4 * Z1) / 2
                   = 2m * Z1 = 100 mm
                    Z1 = 100 mm / (2 * m)
   
   Assuming m = 2
5 mm (we can adjust it depending on what standard gears are available):
   
   Z1 = 100 mm / (2 * 2
5 mm) = 20
   Therefore, Z1 could be set to 20 (assuming that it meets other design criteria such as strength and space constraints), and Z2 would then be 60.

   With these values:
   
   - Gear 1 pitch diameter: m * Z1 = 2
5 mm * 20 = 50 mm
   - Gear 2 pitch diameter: m * Z2 = 2
5 mm * 60 = 150 mm
   - Center distance: (50 mm / 2) + (150 mm / 2) = 100 mm
   
   Finally, the coordinates of the center of the driven gear (Gear 2) relative to the driving gear (Gear 1) with (0,0) will be (100, 0) mm along the axis of gear rotation.

In our final configuration for a 3:1 ratio and a 100 mm center distance:

- Module (m): 2.5 mm
- Driving gear (Gear 1): 20 teeth, pitch diameter 50 mm, coordinates (0,0)
- Driven gear (Gear 2): 60 teeth, pitch diameter 150 mm, coordinates (100,0)

Please note that the actual design of a gear train would consider additional factors such as the torque handling capability, material strength, geometrical constraints, and manufacturing standards
It is often necessary to iterate on the design parameters to fulfill all the system's requirements
