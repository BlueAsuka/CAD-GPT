To design this gear system, we need to establish the basic geometric and kinematic relationships between the two gears. Here's how we can compute the parameters step by step.

Given the following information:
- Helical gears with a 30-degree pitch angle (α)
- Center distance (A) between gear axes: 50mm
- Gear ratio (i): 1.5:1
- The height of gear teeth are irrelevant in gear ratio calculations
- Driving gear centered at coordinate (0, 0)

### Step 1: Determine the Gear Ratio
The gear ratio (i) is given by the ratio of the number of teeth on the driven gear (N2) to the number of teeth on the driving gear (N1):

\[ i = \frac{N2}{N1} \]

With the desired gear ratio being 1.5:1, we get:

\[ i = 1.5 = \frac{N2}{N1} \]

### Step 2: Calculate the Number of Teeth
For standard gear systems, the number of teeth should ideally be a reasonable whole number to make manufacturing simpler. The precise number of teeth depends on other factors, including the module and pitch diameter.

### Step 3: Calculate the Module
The module (m) can be related to the pitch diameter (d) and number of teeth (N) using the formula:

\[ m = \frac{d}{N} \]

The center distance (A) is related to the pitch diameters (d1 and d2) of the two gears:

\[ A = \frac{d1 + d2}{2} \]

Since \( A = 50mm \) and \( i = \frac{N2}{N1} = 1.5 \), we can choose an appropriate number of teeth for the driving gear (N1) and calculate N2 using the gear ratio:

\[ N2 = i \cdot N1 \]

Let's assume N1 is 20 (a reasonable choice for practical gear design, giving us whole numbers while considering the standard manufacturing capabilities). Then we calculate N2:

\[ N2 = 1.5 \cdot 20 = 30 \]

### Step 4: Determine the Module Based on Center Distance
Now we need to select an appropriate module (m) which satisfies our size constraints. Based on the above formula for the center distance:

\[ 50mm = \frac{d1 + d2}{2} = \frac{m \cdot (N1 + N2)}{2} \]

Plugging in the values for N1 and N2:

\[ 50mm = \frac{m \cdot (20 + 30)}{2} \]

From this, we can solve for m:

\[ m = \frac{100mm}{50} = 2mm \]

However, 2mm is not in the priority list of module numbers. We must round to the nearest preferred module number. The closest is 2mm, which is already a preferred number, so we will use that.

### Step 5: Calculate Pitch Diameters
Now that we know the module (m = 2mm), we can find the pitch diameters (d1 and d2):

\[ d1 = m \cdot N1 = 2mm \cdot 20 = 40mm \]
\[ d2 = m \cdot N2 = 2mm \cdot 30 = 60mm \]

### Step 6: Determine the Coordinates of the Driven Gear
Since the driving gear is at the origin (0,0), and the axes are 50mm apart (A = 50mm), the center of the driven gear (gear 2) will be:

\[ (x2, y2) = (50mm, 0) \]

This is because they are on the same horizontal line, and the distance between centers is the same as A.

### Step 7: Verify the Calculations
Let's verify the calculations with the given center distance A:

\[ A = \frac{d1 + d2}{2} = \frac{40mm + 60mm}{2} = 50mm \]

This matches our given center distance, so the verification is successful.

### Final Result:
- gear 1 (driving gear): helical gear, module 2mm, 20 teeth, pitch diameter 40mm, coordinate (0, 0)
- gear 2 (driven gear): helical gear, module 2mm, 30 teeth, pitch diameter 60mm, coordinate (50, 0)

The result satisfies the gear ratio of 1.5:1 and adheres to the given requirements and constraints.