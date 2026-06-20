# backend/profile.py — step 2: mask -> symmetry axis -> radius profile r(h)
import json
import numpy as np
import cv2
import matplotlib.pyplot as plt

mask = cv2.imread("mask.png", cv2.IMREAD_GRAYSCALE)
binary = (mask > 127).astype(np.uint8)          # crisp black/white

# keep only the largest white blob (drops stray specks or shadow bits)
n, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])   # skip background (label 0)
binary = (labels == largest).astype(np.uint8)

# which rows (heights) actually contain the vase
rows = np.where(binary.any(axis=1))[0]
top, bottom = rows.min(), rows.max()

heights, radii, centers = [], [], []
for row in range(top, bottom + 1):
    cols = np.where(binary[row] > 0)[0]          # white pixels in this row
    if cols.size == 0:
        continue
    left, right = cols.min(), cols.max()
    radii.append((right - left) / 2.0)           # half the width = radius here
    centers.append((right + left) / 2.0)         # midpoint of this row
    heights.append(bottom - row)                 # height measured up from the base

heights = np.array(heights, float)
radii   = np.array(radii, float)
axis_x  = float(np.median(centers))              # the vertical symmetry axis

with open("profile.json", "w") as f:
    json.dump({"heights": heights.tolist(), "radii": radii.tolist(),
               "axis_x": axis_x, "units": "pixels"}, f)
print(f"saved profile.json — {len(heights)} samples, axis_x = {axis_x:.1f}px")

# ---- visualize ----
fig, ax = plt.subplots(1, 2, figsize=(12, 6))
rows_plot = bottom - heights

ax[0].imshow(binary, cmap="gray")
ax[0].axvline(axis_x, color="red", lw=1.5)                      # symmetry axis
ax[0].plot(axis_x + radii, rows_plot, color="cyan", lw=1.5)    # right edge
ax[0].plot(axis_x - radii, rows_plot, color="cyan", lw=1.5)    # left edge
ax[0].set_title("mask + axis (red) + detected silhouette (cyan)")
ax[0].axis("off")

ax[1].plot(radii, heights, color="#2c63d6")
ax[1].set_title("profile  r(h)")
ax[1].set_xlabel("radius (px)"); ax[1].set_ylabel("height from base (px)")
ax[1].set_aspect("equal"); ax[1].grid(alpha=0.3)

plt.tight_layout()
plt.show()