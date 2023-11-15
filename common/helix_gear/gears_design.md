To design a one-stage helical gear system that meets the given requirements, we'll follow these steps:

1. Determine the gear ratio.
2. Select a module number.
3. Calculate the number of teeth for both gears.
4. Determine the pitch diameters.
5. Calculate the center distance.
6. Determine the coordinates of the driven gear.

### Step 1: Determine Gear Ratio

The desired gear ratio is given as 1.5:1, which means that the driving gear must make 1.5 revolutions for every revolution of the driven gear.

Let us denote:
- $ N_1 $ as the number of teeth for the driving gear.
- $ N_2 $ as the number of teeth for the driven gear.
- $ i $ as the gear ratio.

Therefore, the gear ratio $ i $ can be described as:
$$ i = \frac{N_2}{N_1} $$

Given that $$ i = 1.5 $$ we can select an initial pair of teeth numbers that closely fit this ratio.

### Step 2: Select a Module Number

The module number is crucial to define the gear size and is related to the pitch diameter and the number of teeth via the equation:

$$ module = \frac{pitch \ diameter}{number \ of \ teeth} $$

For our initial calculation we can start with a module of 1mm as an example, from this we will see if it fits and adjust as necessary.

### Step 3: Calculate Number of Teeth for Both Gears

To satisfy the gear ratio of 1.5, and starting with a standard number of teeth for the smaller gear, say 20 (a typical selection for smaller gears), the number of teeth on the larger gear should be:

$$ N_2 = N_1 \times i = 20 \times 1.5 = 30 $$

So we have 20 teeth on the driving gear and 30 teeth on the driven gear.

### Step 4: Determine the Pitch Diameters

The pitch diameter (D) for each gear can be calculated using the module (m) and the number of teeth (N):

$$ D = m \times N $$

For the driving gear:
$$ D_1 = m \times N_1 = 1 \times 20 = 20mm $$

For the driven gear:
$$ D_2 = m \times N_2 = 1 \times 30 = 30mm $$

### Step 5: Calculate the Center Distance

The center distance (a) for helical gears is given by the sum of the pitch diameters of the two gears divided by 2:

$$ a = \frac{D_1 + D_2}{2} $$

$$ a = \frac{20mm + 30mm}{2} = 25mm $$

### Step 6: Coordinates of the Driven Gear

Since the driving gear is located at the center of the plane, which is (0,0), and the distance between the axes is 50mm, the driven gear must then be displaced by 50mm along the x-axis.

The coordinates of the driven gear center would then be (50, 0).

### Review and Finalizing

Now, we must check if the center distance (calculated as 25mm) matches the given condition (50mm). If not, we must adjust the module or the number of teeth to meet this distance and still maintain or exceed the desired gear ratio and ensure that the modules coincide with the priority or alternate numbers.

In our case, the calculated center distance does not match the required center distance of 50mm, so we must adjust our values.

To get a center distance of 50mm, let's increase our module to match this. We choose a pair of teeth numbers that maintain the gear ratio above 1.5, and the module then matches the product of half the center distance and sum of teeth number as follows:

$$ m = \frac{2 \times a}{N_1 + N_2} $$

We keep the numbers of teeth the same for initial calculation:
$$ m = \frac{2 \times 50mm}{20 + 30} $$
$$ m = \frac{100}{50} = 2mm $$

The module of 2 is a number from the priority list, which is good. Now we recalculate the pitch diameters with this new module:

For the driving gear:
$$ D_1 = 2 \times 20 = 40mm $$

For the driven gear:
$$ D_2 = 2 \times 30 = 60mm $$

Now we check the center distance:
$$ a = \frac{D_1 + D_2}{2} = \frac{40mm + 60mm}{2} = \frac{100mm}{2} = 50mm $$

The center distance is correct, so our parameters are chosen properly. 

With these new parameters, we have:

gear 1 (driving gear): helical gear, module 2mm, teeth 20, pitch diameter 40mm, helix angle 20 degrees, height 15mm, coordinate (0, 0)
gear 2 (driven gear): helical gear, module 2mm, teeth 30, pitch diameter 60mm, helix angle 20 degrees, height 20mm, coordinate (50, 0)

The gear ratio now is actually:
$$ i = \frac{N_2}{N_1} = \frac{30}{20} = 1.5 $$

So the design meets the required gear ratio.