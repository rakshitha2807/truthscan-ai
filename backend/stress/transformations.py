"""Create controlled, clearly labelled alterations of an input image."""
from pathlib import Path
from PIL import Image, ImageFilter

def create_stress_variants(image_path, output_dir):
    image_path = Path(image_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    original = Image.open(image_path).convert("RGB")
    width, height = original.size
    results = []

    # JPEG recompression at three quality levels.
    for quality in (90, 60, 30):
        out = output_dir / f"recompressed_q{quality}.jpg"
        original.save(out, "JPEG", quality=quality, optimize=True)
        results.append({"test": "recompression", "setting": f"quality={quality}", "path": str(out)})

    # Resize down, then restore to the original dimensions for a fair comparison.
    for percent in (75, 50, 25):
        small_size = (max(1, int(width * percent / 100)),
                      max(1, int(height * percent / 100)))
        small = original.resize(small_size, Image.Resampling.LANCZOS)
        restored = small.resize((width, height), Image.Resampling.LANCZOS)
        out = output_dir / f"resized_{percent}pct.png"
        restored.save(out)
        results.append({"test": "resizing", "setting": f"downscale={percent}%", "path": str(out)})

    # Center crops retaining 90%, 75%, and 60% of each dimension.
    for retain in (90, 75, 60):
        crop_w = max(1, int(width * retain / 100))
        crop_h = max(1, int(height * retain / 100))
        left = (width - crop_w) // 2
        top = (height - crop_h) // 2
        cropped = original.crop((left, top, left + crop_w, top + crop_h))
        out = output_dir / f"crop_retain_{retain}pct.png"
        cropped.save(out)
        results.append({
            "test": "cropping", "setting": f"retained_dimensions={retain}%",
            "path": str(out), "crop_box": [left, top, left + crop_w, top + crop_h]
        })

    # Increasing Gaussian blur radius.
    for radius in (1, 2, 4):
        out = output_dir / f"blur_radius_{radius}.png"
        original.filter(ImageFilter.GaussianBlur(radius=radius)).save(out)
        results.append({"test": "blur", "setting": f"radius={radius}", "path": str(out)})

    return results
