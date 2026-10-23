# Mano Izq: rebuilding it parametrically in SolidWorks 2025

All numbers come from the final model (`Mano Izq - SolidWorks.STL`). They're in **your SLDPRT's coordinates**:

- **Y**: the horizontal coordinate of Croquis6. Positive is the pinky side, negative is the thumb side.
- **Z**: height. Wrist at -15, tip of the middle finger at 152.7.
- **X**: thickness. Negative is the back of the hand (dorsal), positive is the palm side.

Units are mm. You can check the overlay against the STL, whose bounding box is 167.7 × 117.3 × 38.6.

Each part of the model maps to one SolidWorks operation:

| Part | Operation |
|---|---|
| Wrist + palm | Recubrir with 10 sections + guide curves |
| Top of the palm | Extruir corte along the knuckle line + Redondeo |
| Each finger and the thumb | Revolución of 4 tangent circles (the tip comes out round by itself) |
| Thenar pad | Revolución of a half-ellipse + Escala |
| Joints | Combinar → Agregar + variable-size Redondeo |
| Nails and palm lines | Envolver (Repujado / Grabado) |

## 0. Preparation
1. Open `Mano Izq..SLDPRT` → *Guardar como* `Mano Izq v2.SLDPRT`. Keep Croquis6 and your side profile.
2. Delete Recubrir2 and the failed operations. Suppress Recubrir1 too, because the new Recubrir includes the wrist.
3. Make an assembly called `Comparación` with `Mano Izq v2` and `Mano Izq - SolidWorks.STL`, both fixed at the origin, with the STL at 60% transparency. You'll use it to compare as you go.

## 1. Global variables (Herramientas → Ecuaciones)
Create one variable per value in the tables, for example `"R0_medio" = 8.1`. In each dimension, type `=` and pick the variable. To change the hand later, you only edit this table.

## 2. Palm and wrist (Recubrir)
Planes parallel to *Alzado* (normal = Z) at these heights. On each plane, a **closed sketch**:
- **Wrist rows (Z = -15 and 10):** an ellipse.
- **Palm rows:** a "stadium" shape. Draw it as two lines plus two *Elipse parcial*. The thumb-side end has a semi-axis of 13 mm and the pinky-side end 20 mm, both measured along Y.

| Z | Y from (thumb side) | Y to (pinky side) | X dorsal | X palm |
|---|---|---|---|---|
| -15 | -25.5 | 25.5 | -19.0 | 19.0 |
| 10 | -24.6 | 24.6 | -18.3 | 15.6 |
| 25 | -29.9 | 28.8 | -17.3 | 12.0 |
| 35 | -35.3 | 31.7 | -16.4 | 12.6 |
| 45 | -39.6 | 34.0 | -15.8 | 13.0 |
| 55 | -44.0 | 35.1 | -16.1 | 12.6 |
| 65 | -44.0 | 37.5 | -16.8 | 11.5 |
| 75 | -28.0 | 38.0 | -16.9 | 9.9 |
| 85 | -24.0 | 33.0 | -15.9 | 6.5 |
| 97 | -20.0 | 28.0 | -15.3 | 4.5 |

**Guide curves**, each an open spline that must pierce every section with *Perforación*, as on the seat:
- **Pinky-side guide:** *Convertir entidades* of the pinky-side edge of Croquis6 + *Recortar*.
- **Thumb-side guide:** a new spline through the "Y from" column.
- **Dorsal and palm guides:** splines through the "X dorsal" and "X palm" columns, in a plane perpendicular to Croquis6 at Y ≈ 4.

**Recubrir:** profiles from Z -15 to 97 in order, the 4 curves under *Curvas guía*, and **uncheck Fusionar resultado**.

## 3. Top of the palm
1. Sketch on the plane of Croquis6: a closed polygon **above** the knuckle line, through these points (Y, Z):
   - (90, 96) → (39.3, 71) → (29.9, 88.5) → (12.3, 96.9) → (-5, 97.5) → (-24, 80) → (-31, 71.5) → (-49.5, 72) → (-90, 62)
   - Close it upward at Z = 300.
2. *Extruir corte* → **Por todo – ambas direcciones**, only on the palm body.

## 4. Fingers and thumb (Revolución): the fix for the tip
For each finger:
1. In Croquis6, draw the **axis line** from the root center to the tip center (Y, Z values from the table).
2. Make a **plane**: 1st reference = that line, 2nd reference = the plane of Croquis6, **Perpendicular**.
3. Sketch on that plane:
   - A centerline along the axis.
   - 4 circles centered on the axis at distances d0 to d3, with radii R0 to R3.
   - The **tangent lines** joining the circles on one side.
   - *Recortar* until you have the closed half-profile against the centerline.
4. *Revolución* 360° about the centerline, with *Fusionar resultado* unchecked.
   - The last circle forms the tip, already round. The tip of Croquis6 = tip center + R3.
5. **Optional:** *Escala* on that body only, about its centroid, with X = 0.92 (the finger is about 8% thinner than it is wide).

| Finger | Root center (Y, Z, X) | Tip center (Y, Z, X) | d0 / d1 / d2 / d3 | R0 / R1 / R2 / R3 | Nail L × W |
|---|---|---|---|---|---|
| Pinky | 28.4, 64.8, -8.1 | 53.2, 107.8, -13.4 | 0 / 27.5 / 39.2 / 50.1 | 5.8 / 5.9 / 5.4 / 5.0 | 6.3 × 7.2 |
| Ring | 19.2, 84.6, -7.1 | 31.1, 135.6, -12.8 | 0 / 24.7 / 39.2 / 52.8 | 7.7 / 6.8 / 5.6 / 5.6 | 7.0 × 8.0 |
| Middle | 3.9, 89.1, -6.8 | 6.0, 146.9, -12.6 | 0 / 27.2 / 43.1 / 58.2 | 8.1 / 7.2 / 6.1 / 5.8 | 7.3 × 8.4 |
| Index | -16.7, 81.6, -6.4 | -15.9, 141.4, -12.4 | 0 / 28.2 / 44.7 / 60.3 | 8.5 / 7.6 / 6.0 / 5.8 | 7.3 × 8.4 |
| Thumb | -25.8, 34.0, 6.0 | -52.8, 95.0, 4.0 | 0 / 31.9 / 54.7 / 66.9 | 10 / 8.5 / 7.5 / 6.4 | 8.9 × 9.2 |

- d = distance along the axis to the station: root, middle knuckle, last knuckle, tip center.
- R = radius at that station.
- The fingers start about 10 mm inside the palm. That overlap is what lets the Combinar work.

## 5. Thenar pad (the bulge at the base of the thumb)
1. Plane parallel to Croquis6 at X = 7.5.
2. Half-ellipse with semi-axis 18 (vertical, along Z) and 14 (along Y), centered at (Y -22, Z 42), plus a vertical centerline.
3. *Revolución*, then *Escala* X = 0.71 about the centroid. Result: radii of 14 × 10 × 18.

## 6. Join and fillet
1. *Insertar → Características → Combinar → **Agregar*** for all the bodies.
2. *Redondeo*, **largest radii first**:
   - Palm top edge (where the cut was), **variable size**: about 8 on the palm side and about 5 on the back.
   - Finger–palm joints: r 3 on the back, r 6 on the palm side (variable size).
   - Thenar pad joint: r 6.
   - Webs between fingers: r 2.
   - If a fillet fails, lower it 1 mm or use *FilletXpert*.

## 7. Details (at the very end)
- **Nails:**
  - A plane tangent to the back of the last phalanx.
  - A rounded rectangle L × W from the table, ending about 2 mm past the tip center.
  - *Envolver* → **Repujado 0.2 mm**, method *Superficie spline*, onto that face.
- **Palm lines:**
  - A plane parallel to Croquis6 at X = +25.
  - A spline through these points, then *Desplazar entidades* 0.5 mm **bidirectional + Tapar extremos**.
  - *Envolver* → **Grabado 0.45 mm** onto the palm.
  - Heart: (29, 73) (22, 75) (14, 78) (6, 82.5) (-2, 87.5)
  - Head: (-35, 70) (-22, 67) (-8, 63) (8, 60) (25, 57)
  - Life: (-33, 69) (-25, 62) (-18, 54) (-13, 44) (-10, 35) (-10, 30)
- **Knuckles (optional):**
  - A small ellipsoid (revolve + scale) on the back of each finger root.
  - Its center is 3 mm along the axis and 0.6 × R0 toward the back. Radii: 0.55·R0 across, 3 mm in thickness, 4.5 mm along the axis.
  - Then a fillet of r 2.

## 8. Measurements that improve it (optional, with a caliper)
These replace values in the global-variables table:
- **Each finger:** width at the root, the middle knuckle and the last knuckle (= 2·R). Thickness at the same points (thickness ÷ width = the Escala factor).
- **Palm thickness:** at the knuckles and at mid-palm.
- **Wrist:** width and thickness.
