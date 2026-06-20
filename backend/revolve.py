# backend/revolve.py — step 3: fit r(h) and revolve it into a 3D model
import json
import numpy as np
from scipy.interpolate import UnivariateSpline
import matplotlib.pyplot as plt

prof = json.load(open("profile.json"))
h = np.array(prof["heights"], float)
r = np.array(prof["radii"], float)

order = np.argsort(h)            # extractor gave top->base; sort base->top
h, r = h[order], r[order]

# fit a smooth spline through the noisy profile (raise s for more smoothing)
spline = UnivariateSpline(h, r, s=len(h) * 9)

# resample the smooth profile evenly along the height
H = np.linspace(h.min(), h.max(), 200)
R = np.clip(spline(H), 0, None)          # radius can't go negative

# ---- revolve: every height h gets a circle of radius r(h) ----
#   (theta, h)  ->  [ r(h)*cos(theta), r(h)*sin(theta), h ]
theta = np.linspace(0, 2 * np.pi, 120)
T, Hgrid = np.meshgrid(theta, H)
X = R[:, None] * np.cos(T)
Y = R[:, None] * np.sin(T)
Z = Hgrid

# ---- view ----
fig = plt.figure(figsize=(13, 6))

axp = fig.add_subplot(1, 2, 1)
axp.plot(r, h, lw=1, color="#bbbbbb", label="raw")
axp.plot(R, H, lw=2, color="#2c63d6", label="spline")
axp.set_title("profile: raw vs smooth spline")
axp.set_xlabel("radius (px)"); axp.set_ylabel("height (px)")
axp.set_aspect("equal"); axp.legend(); axp.grid(alpha=0.3)

ax3 = fig.add_subplot(1, 2, 2, projection="3d")
ax3.plot_surface(X, Y, Z, color="#6ba8ff", edgecolor="none")
ax3.set_title("revolved 3D model")
ax3.set_box_aspect((R.max() * 2, R.max() * 2, H.max()))
ax3.set_axis_off()

plt.tight_layout()
plt.show()

json.dump({"heights": H.tolist(), "radii": R.tolist()}, open("profile_fit.json", "w"))
print("saved profile_fit.json")