"""Run all image stress tests and save a JSON results file."""
import argparse
import json
from pathlib import Path
from transformations import create_stress_variants
from metrics import compare_images

def run_stress_tests(image_path, output_dir):
    output_dir = Path(output_dir)
    variants_dir = output_dir / "variants"
    output_dir.mkdir(parents=True, exist_ok=True)
    variants = create_stress_variants(image_path, variants_dir)

    results = []
    for item in variants:
        metrics = compare_images(image_path, item["path"], item.get("crop_box"))
        results.append({**item, "metrics": metrics})

    result_path = output_dir / "stress_results.json"
    result_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results, result_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TruthScan AI image stress testing")
    parser.add_argument("image", help="Path to the original screenshot/image")
    parser.add_argument("--output", default="stress_output", help="Output folder")
    args = parser.parse_args()
    rows, saved = run_stress_tests(args.image, args.output)
    print(f"Created {len(rows)} altered images.")
    print(f"Results saved to: {saved}")
    for row in rows:
        m = row["metrics"]
        print(f'{row["test"]:12} {row["setting"]:28} PSNR={m["psnr_db"]:.2f} dB  SSIM={m["ssim"]:.4f}')
