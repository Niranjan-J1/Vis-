# backend/server.py — serves the frontend AND runs the photo -> profile pipeline
import io, os
import numpy as np
import cv2
from PIL import Image
from scipy.ndimage import binary_fill_holes, median_filter
from scipy.signal import savgol_filter
from rembg import remove, new_session
from flask import Flask, request, jsonify, send_from_directory
 
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, static_folder=os.path.join(BASE, "frontend"), static_url_path="")
 
SESSION = new_session("isnet-general-use")   # swap to "birefnet-general-lite" for sharper edges (slower on CPU)
 
def photo_to_profile(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
 
    mask = np.array(remove(img, session=SESSION, only_mask=True, post_process_mask=True))
    binary = (mask > 127).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    if n > 1:
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        binary = (labels == largest).astype(np.uint8)
    binary = binary_fill_holes(binary).astype(np.uint8)
 
    rows = np.where(binary.any(axis=1))[0]
    top, bottom = rows.min(), rows.max()
    H, R = [], []
    for row in range(top, bottom + 1):
        cols = np.where(binary[row] > 0)[0]
        if cols.size == 0:
            continue
        H.append(bottom - row)
        R.append((cols.max() - cols.min()) / 2.0)
    H = np.array(H, float); R = np.array(R, float)
    order = np.argsort(H); H, R = H[order], R[order]
 
    # 3) feature-preserving smoothing: median kills spikes, Savitzky-Golay
    #    smooths noise while KEEPING real features like the neck.
    R = median_filter(R, size=7)
    win = max(11, len(R) // 15)
    if win % 2 == 0: win += 1
    win = min(win, len(R) - 1 + (len(R) % 2))      # keep odd and <= len
    if win >= 5:
        R = savgol_filter(R, win, 3)
    Hs = np.linspace(H.min(), H.max(), 200)
    Rs = np.clip(np.interp(Hs, H, R), 0, None)
 
    props = {
        "height":       float(Hs.max() - Hs.min()),
        "maxDiameter":  float(Rs.max() * 2),
        "baseDiameter": float(Rs[0] * 2),
        "neckDiameter": float(Rs[int(len(Rs) * 0.6):].min() * 2),
        "volume":       float(np.trapezoid(np.pi * Rs**2, Hs)),
    }
    return {"heights": Hs.tolist(), "radii": Rs.tolist(), "properties": props}
 
@app.route("/api/model", methods=["POST"])
def model():
    return jsonify(photo_to_profile(request.files["image"].read()))
 
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")
 
if __name__ == "__main__":
    app.run(port=8000, debug=True)