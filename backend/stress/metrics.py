"""Measure image differences. These metrics describe change, not authenticity."""
from pathlib import Path
from PIL import Image
import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

def _sharpness(image):
    gray = np.asarray(image.convert("L"), dtype=np.float64)
    # Variance of a simple Laplacian response: a rough sharpness indicator.
    lap = (-4 * gray
           + np.roll(gray, 1, axis=0) + np.roll(gray, -1, axis=0)
           + np.roll(gray, 1, axis=1) + np.roll(gray, -1, axis=1))
    return float(np.var(lap))

def compare_images(original_path, altered_path, crop_box=None):
    original = Image.open(original_path).convert("RGB")
    altered = Image.open(altered_path).convert("RGB")

    if crop_box:
        reference = original.crop(tuple(crop_box))
    else:
        reference = original

    # For non-crop tests, variants should already be restored to original size.
    # For crop tests, compare against the corresponding original region.
    if reference.size != altered.size:
        altered = altered.resize(reference.size, Image.Resampling.LANCZOS)

    a = np.asarray(reference, dtype=np.uint8)
    b = np.asarray(altered, dtype=np.uint8)

    psnr = float(peak_signal_noise_ratio(a, b, data_range=255))
    ssim = float(structural_similarity(a, b, channel_axis=2, data_range=255))
    return {
        "original_dimensions": list(reference.size),
        "altered_dimensions": list(Image.open(altered_path).size),
        "original_bytes": Path(original_path).stat().st_size,
        "altered_bytes": Path(altered_path).stat().st_size,
        "psnr_db": psnr,
        "ssim": ssim,
        "original_sharpness": _sharpness(reference),
        "altered_sharpness": _sharpness(Image.open(altered_path).convert("RGB")),
    }
