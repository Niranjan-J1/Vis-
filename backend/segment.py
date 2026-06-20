# backend/segment.py — step 1 of the photo pipeline: photo -> clean object mask
import sys
from PIL import Image
import matplotlib.pyplot as plt
from rembg import remove

# pass an image path, or default to test_vase.jpg in the project root
path = sys.argv[1] if len(sys.argv) > 1 else "test_vase.jpg"
img = Image.open(path).convert("RGB")

# rembg runs a pretrained segmentation net (U2-Net) and returns:
cutout = remove(img)                    # RGBA: object kept, background made transparent
mask   = remove(img, only_mask=True)    # grayscale: white = object, black = background

cutout.save("cutout.png")
mask.save("mask.png")
print("saved cutout.png and mask.png")

# look at all three side by side
fig, ax = plt.subplots(1, 3, figsize=(14, 5))
ax[0].imshow(img);    ax[0].set_title("input photo");          ax[0].axis("off")
ax[1].imshow(mask, cmap="gray"); ax[1].set_title("mask (object = white)"); ax[1].axis("off")
ax[2].imshow(cutout); ax[2].set_title("cutout");               ax[2].axis("off")
plt.tight_layout()
plt.show()