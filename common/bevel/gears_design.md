To design a one-stage bevel gear system with a gear ratio of 2:1, we need to determine the module, number of teeth for both gears, pitch angles, and the spatial coordinates of the driven gear center.

### Step 1: Gear Ratio and Teeth Number
Given the desired gear ratio (GR) of 2:1, we can express this as:
$$ GR = \frac{N_2}{N_1} = 2 $$

Where:
- \( N_1 \) = Number of teeth on the driving gear
- \( N_2 \) = Number of teeth on the driven gear

Since the gear ratio is 2:1, we can choose a convenient number of teeth for the driving gear (\( N_1 \)) and calculate \( N_2 \) accordingly. Let's assume \( N_1 \) to be 20 (a common standard number for gear teeth), then \( N_2 \) would be:
$$ N_2 = GR \times N_1 = 2 \times 20 = 40 $$

### Step 2: Module Calculation
The module (m) is a measure of the size of the teeth and is related to the pitch diameter (D) and the number of teeth (N) by the formula:
$$ m = \frac{D}{N} $$

However, we do not have the pitch diameters yet. The module is typically chosen based on standard sizes and the space available in the application. For this example, let's choose a module that will give us reasonable pitch diameters for both gears. We can start with a module of 2 mm and adjust if necessary.

### Step 3: Pitch Diameter
With the module and number of teeth, we can calculate the pitch diameters for both gears:
$$ D_1 = m \times N_1 = 2 \times 20 = 40 \text{ mm} $$
$$ D_2 = m \times N_2 = 2 \times 40 = 80 \text{ mm} $$

### Step 4: Pitch Angles
The pitch angle (\( \beta \)) for bevel gears is related to the gear ratio and is defined as the angle between the gear axis and the element of the pitch cone (the cone that defines the pitch surface of the gear). For the driving gear, the pitch angle is given as 45 degrees. The pitch angle for the driven gear can be calculated using the gear ratio and the fact that the sum of the pitch angles of both gears should be 90 degrees (since they are bevel gears and meet at an angle):
$$ \beta_1 + \beta_2 = 90^\circ $$
$$ \beta_2 = 90^\circ - \beta_1 = 90^\circ - 45^\circ = 45^\circ $$

### Step 5: Helix Angle
The helix angle (\( \psi \)) for the driving gear is given as 0 degrees. Since these are bevel gears and not helical bevel gears, the helix angle for both gears will be 0 degrees.

### Step 6: Gear Coordinates
The driving gear is located at the spatial coordinate (0, 0, 0). The driven gear will be positioned such that its center is on the pitch diameter of the driving gear and at the correct angle. Since the gears meet at their pitch diameters and the pitch angle is 45 degrees, the driven gear's center will be along the line that is at 45 degrees to the axis of the driving gear. The distance from the origin will be half the pitch diameter of the driven gear (since the pitch diameters meet at a point), which is \( \frac{D_2}{2} = \frac{80}{2} = 40 \) mm.

The coordinates of the driven gear center in spatial coordinates can be calculated using trigonometry, considering the pitch angle of 45 degrees. However, since the pitch angle is 45 degrees, the x and y coordinates will be equal. Therefore, the coordinates of the driven gear center will be (40, 0, 40).

### Final Result
After reviewing the parameters, we have:

gear 1 (driving gear): bevel gear, module 2mm, teeth 20, pitch diameter 40mm, pitch angle 45 degrees, helix angle 0 degrees, height 20mm, coordinate (0, 0, 0)  
gear 2 (driven gear): bevel gear, module 2mm, teeth 40, pitch diameter 80mm, pitch angle 45 degrees, helix angle 0 degrees, height 20mm, coordinate (40, 0, 40)

These parameters satisfy the user's requirements for a gear ratio of 2:1, equal pitch angles of 45 degrees, and the specified heights and pressure angles.