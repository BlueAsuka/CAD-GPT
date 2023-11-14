To design a gear system with the given requirements, we need to determine the module, number of teeth, and the coordinates of the driven gear center. Let's start by defining the gear ratio and the basic gear equation.

### Step 1: Gear Ratio
The gear ratio (i) is given as 2:1, which means the driven gear must have twice as many teeth as the driving gear.

### Step 2: Basic Gear Equation
The basic gear equation relates the module (m), number of teeth (Z), and pitch diameter (d) as follows:

$$ d = m \cdot Z $$

### Step 3: Center Distance
The center distance (a) between the two gears is given as 60mm. For a gear ratio of 2:1, the pitch diameters of the gears must satisfy the following relationship:

$$ a = \frac{d_{driving} + d_{driven}}{2} $$

Given that the gear ratio is 2:1, we can express the pitch diameters in terms of the module and number of teeth:

$$ a = \frac{m \cdot Z_{driving} + m \cdot 2 \cdot Z_{driving}}{2} $$
$$ a = \frac{m \cdot Z_{driving} (1 + 2)}{2} $$
$$ a = \frac{3 \cdot m \cdot Z_{driving}}{2} $$

Since the center distance a is 60mm, we can solve for m in terms of Z_{driving}:

$$ 60 = \frac{3 \cdot m \cdot Z_{driving}}{2} $$
$$ m = \frac{2 \cdot 60}{3 \cdot Z_{driving}} $$
$$ m = \frac{40}{Z_{driving}} $$

### Step 4: Selecting Module and Teeth Number
We need to select a module and number of teeth for the driving gear that satisfies the gear ratio and the center distance. We also need to ensure that the module is one of the preferred values.

Let's assume a reasonable number of teeth for the driving gear, say 20 teeth (which is common for such gears). Then we can calculate the module:

$$ m = \frac{40}{20} $$
$$ m = 2 $$

The module of 2 is a preferred value, so we can proceed with this choice.

### Step 5: Calculating Gear Parameters
Now we can calculate the pitch diameters and the coordinates of the driven gear center.

For the driving gear:
$$ d_{driving} = m \cdot Z_{driving} $$
$$ d_{driving} = 2 \cdot 20 $$
$$ d_{driving} = 40mm $$

For the driven gear (with twice the number of teeth):
$$ Z_{driven} = 2 \cdot Z_{driving} $$
$$ Z_{driven} = 2 \cdot 20 $$
$$ Z_{driven} = 40 $$

$$ d_{driven} = m \cdot Z_{driven} $$
$$ d_{driven} = 2 \cdot 40 $$
$$ d_{driven} = 80mm $$

### Step 6: Coordinates of the Driven Gear Center
The driving gear is at the center of the plane (0, 0). The driven gear must be positioned at a distance equal to the center distance (60mm) from the driving gear along the x-axis.

The y-coordinate remains the same since the axes are parallel.

### Final Result
gear 1 (driving gear): herringbone gear, module 2mm, 20 teeth, pitch diameter 40mm, height 25mm, pressure angle 20 degrees, coordinate (0,0)
gear 2 (driven gear): herringbone gear, module 2mm, 40 teeth, pitch diameter 80mm, height 16mm, pressure angle 20 degrees, coordinate (60,0)