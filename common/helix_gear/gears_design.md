To design a gear system with the given requirements, we need to calculate the module, number of teeth, and the coordinates of the driven gear center. Let's start by defining the gear ratio and the relationship between the gears.

### Gear Ratio
The gear ratio (i) is defined as the ratio of the number of teeth on the driven gear (N2) to the number of teeth on the driving gear (N1):

$$ i = \frac{N2}{N1} $$

Given that the desired gear ratio is 1.5:1, we can express N2 in terms of N1:

$$ N2 = 1.5 \cdot N1 $$

### Module Calculation
The module (m) is a measure of the size of the teeth and is related to the pitch diameter (d) and the number of teeth (N) by the formula:

$$ m = \frac{d}{N} $$

Since the axes of the two gears are parallel and the center distance (a) is 50mm, we can relate the pitch diameters of the two gears to the center distance:

$$ a = \frac{d1 + d2}{2} $$

Substituting the relationship between d and N, and knowing that d2 = 1.5 * d1, we get:

$$ 50 = \frac{d1 + 1.5 \cdot d1}{2} $$

Solving for d1 gives us:

$$ 50 = d1 \cdot (1 + 1.5) / 2 $$
$$ 50 = d1 \cdot 2.5 / 2 $$
$$ d1 = \frac{50 \cdot 2}{2.5} $$
$$ d1 = 40 \text{mm} $$

Now, we can choose a module that fits the standard sizes and allows us to have an integer number of teeth for the driving gear. Since d1 = m * N1, we can rearrange the formula to find N1:

$$ N1 = \frac{d1}{m} $$

We need to select a module such that N1 is an integer. Let's start with a module of 2mm (a common standard size) and see if it results in an integer number of teeth:

$$ N1 = \frac{40}{2} $$
$$ N1 = 20 $$

This is an integer, so a module of 2mm is suitable. Now we can calculate N2:

$$ N2 = 1.5 \cdot N1 $$
$$ N2 = 1.5 \cdot 20 $$
$$ N2 = 30 $$

### Coordinates of the Driven Gear Center
The driving gear is at the center of the plane (0, 0). The driven gear will be positioned at a distance equal to the center distance (a) along the x-axis. Therefore, the coordinates of the driven gear center will be (50, 0).

### Final Parameters
We have chosen a module of 2mm, which is not a standard size according to the given list. The closest standard size greater than 2mm is 2.5mm. We will use this module and recalculate the number of teeth for both gears.

$$ N1 = \frac{d1}{m} $$
$$ N1 = \frac{40}{2.5} $$
$$ N1 = 16 $$

Now, we calculate N2 using the gear ratio:

$$ N2 = 1.5 \cdot N1 $$
$$ N2 = 1.5 \cdot 16 $$
$$ N2 = 24 $$

Both N1 and N2 are integers, so these values are acceptable. The pitch diameters will be:

$$ d1 = m \cdot N1 $$
$$ d1 = 2.5 \cdot 16 $$
$$ d1 = 40 \text{mm} $$

$$ d2 = m \cdot N2 $$
$$ d2 = 2.5 \cdot 24 $$
$$ d2 = 60 \text{mm} $$

The center distance will be:

$$ a = \frac{d1 + d2}{2} $$
$$ a = \frac{40 + 60}{2} $$
$$ a = 50 \text{mm} $$

This confirms that our choice of module and number of teeth is correct.

### Final Result
gear 1 (driving gear): helical gear, module 2.5mm, teeth 16, pitch diameter 40mm, helix angle 20 degrees, height 15mm, coordinate (0, 0)
gear 2 (driven gear): helical gear, module 2.5mm, teeth 24, pitch diameter 60mm, helix angle 20 degrees, height 20mm, coordinate (50, 0)