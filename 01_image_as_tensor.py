import torch
import torch.nn.functional as F
import numpy as np
from skimage import data
import matplotlib.pyplot as plt
from PIL import Image
import urllib.request

# ── 1. GET AN IMAGE ──────────────────────────────────────────
# Built-in cat photo from scikit-image — no download, no network needed.
img_pil = Image.fromarray(data.chelsea()).convert("RGB")
img_pil = img_pil.resize((256, 256))

# ── 2. IMAGE → TENSOR ────────────────────────────────────────────────────────
# PIL gives us a numpy array of shape [H, W, 3] with values 0-255
# PyTorch expects                      [C, H, W] with values 0.0-1.0
# So we transpose axes and normalize.

img_np = np.array(img_pil)                        # [256, 256, 3]  uint8
img_np = img_np.astype(np.float32) / 255.0        # [256, 256, 3]  float, 0-1
img_tensor = torch.from_numpy(img_np)             # still [256, 256, 3]
img_tensor = img_tensor.permute(2, 0, 1)          # → [3, 256, 256]  C,H,W

print("=== TENSOR SHAPE ===")
print(f"Shape: {img_tensor.shape}")               # torch.Size([3, 256, 256])
print(f"Channels: {img_tensor.shape[0]}")         # 3  (R, G, B)
print(f"Height:   {img_tensor.shape[1]}")         # 256
print(f"Width:    {img_tensor.shape[2]}")         # 256
print(f"Min pixel value: {img_tensor.min():.3f}") # ~0.0
print(f"Max pixel value: {img_tensor.max():.3f}") # ~1.0
print()

# ── 3. LOOK INSIDE A SINGLE CHANNEL ──────────────────────────────────────────
# Pull out just the red channel - it's a plain 2D grid of numbers.
# This is all a grayscale image is. RGB is just 3 of these stacked.
red_channel = img_tensor[0]   # [256, 256]
print("=== RED CHANNEL (top-left 5x5 pixels) ===")
print(red_channel[:5, :5])    # raw float values, each is one pixel's red intensity
print()

# ── 4. DEFINE A CONVOLUTION KERNEL BY HAND ───────────────────────────────────
# A Sobel kernel detects horizontal edges.
# It computes: (pixels below) - (pixels above) at every location.
# Where pixel brightness changes sharply top-to-bottom → large output value → edge.
# Where pixel brightness is uniform → values cancel out → near zero → no edge.
#
# The kernel shape PyTorch needs: [out_channels, in_channels, kH, kW]
# We're going grayscale (1 channel in, 1 channel out), 3x3 kernel.

sobel_horizontal = torch.tensor([
    [-1., -2., -1.],   # weights for row ABOVE current pixel
    [ 0.,  0.,  0.],   # weights for current row (ignored)
    [ 1.,  2.,  1.],   # weights for row BELOW current pixel
]).view(1, 1, 3, 3)    # reshape to [out_ch, in_ch, kH, kW]

sobel_vertical = torch.tensor([
    [-1., 0., 1.],
    [-2., 0., 2.],
    [-1., 0., 1.],
]).view(1, 1, 3, 3)

# ── 5. CONVERT IMAGE TO GRAYSCALE TENSOR ─────────────────────────────────────
# Standard grayscale conversion: weighted sum of R, G, B channels.
# These weights reflect human eye sensitivity (we see green most clearly).
gray = (0.299 * img_tensor[0]
      + 0.587 * img_tensor[1]
      + 0.114 * img_tensor[2])          # [256, 256]

# Conv2d needs shape [batch, channels, H, W] so we add two dimensions
gray_4d = gray.unsqueeze(0).unsqueeze(0)  # [1, 1, 256, 256]

print("=== GRAYSCALE TENSOR SHAPE ===")
print(f"Shape before unsqueeze: {gray.shape}")       # [256, 256]
print(f"Shape after unsqueeze:  {gray_4d.shape}")    # [1, 1, 256, 256]
print()

# ── 6. APPLY THE CONVOLUTION ──────────────────────────────────────────────────
# padding=1 means we pad the border with zeros so output is same size as input.
# This is called "same" padding. Without it, a 3x3 kernel shrinks output by 2px.
edges_h = F.conv2d(gray_4d, sobel_horizontal, padding=1)  # horizontal edges
edges_v = F.conv2d(gray_4d, sobel_vertical,   padding=1)  # vertical edges

# Combine both directions: total edge strength at each pixel
edges = torch.sqrt(edges_h**2 + edges_v**2)  # [1, 1, 256, 256]

# Normalize to 0-1 for display
edges = edges / edges.max()

print("=== CONVOLUTION OUTPUT ===")
print(f"Output shape: {edges.shape}")  # [1, 1, 256, 256] - same spatial size
print(f"Output min:   {edges.min():.3f}")
print(f"Output max:   {edges.max():.3f}")
print()

# ── 7. VISUALIZE ──────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.patch.set_facecolor('#f8f8f6')

axes[0].imshow(img_pil)
axes[0].set_title("Original image\nshape: [3, 256, 256]", fontsize=11)
axes[0].axis('off')

axes[1].imshow(gray.numpy(), cmap='gray')
axes[1].set_title("Grayscale (1 channel)\nshape: [1, 256, 256]", fontsize=11)
axes[1].axis('off')

axes[2].imshow(edges.squeeze().numpy(), cmap='inferno')
axes[2].set_title("After Sobel convolution\nedges detected", fontsize=11)
axes[2].axis('off')

plt.suptitle("An image is a tensor. A convolution is a sliding dot product.",
             fontsize=12, y=1.02)
plt.tight_layout()
plt.savefig("01_output.png", dpi=150, bbox_inches='tight')
plt.show()
print("Saved → 01_output.png")