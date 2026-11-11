
import os
import cv2
import json
import hashlib
import numpy as np
from PIL import Image


# ============================================================
# SHA-256 FINGERPRINT
# ============================================================

def calculate_sha256(image_path):
    sha = hashlib.sha256()

    with open(image_path, "rb") as file:
        for block in iter(lambda: file.read(65536), b""):
            sha.update(block)

    return sha.hexdigest()


# ============================================================
# METADATA
# ============================================================

def extract_metadata(image):
    metadata = {
        "format": image.format,
        "width": image.width,
        "height": image.height,
        "mode": image.mode,
        "exif": {},
        "exif_present": False
    }

    try:
        exif = image.getexif()

        if exif:
            metadata["exif_present"] = True
            metadata["exif"] = {
                str(k): str(v) for k, v in exif.items()
            }
    except Exception:
        pass

    return metadata


# ============================================================
# ERROR LEVEL ANALYSIS
# ============================================================

def perform_ela(image, image_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    name = os.path.splitext(os.path.basename(image_path))[0]

    heatmap_path = os.path.join(output_dir, name + "_ela.png")
    overlay_path = os.path.join(output_dir, name + "_regions.png")
    temp_path = os.path.join(output_dir, name + "_temp.jpg")

    try:
        original = np.array(image.convert("RGB"))

        image.convert("RGB").save(temp_path, "JPEG", quality=90)

        recompressed = np.array(
            Image.open(temp_path).convert("RGB")
        )

        difference = cv2.absdiff(original, recompressed)

        gray = cv2.cvtColor(
            difference, cv2.COLOR_RGB2GRAY
        )

        mean_difference = float(np.mean(gray))
        maximum_difference = float(np.max(gray))

        normalized = cv2.normalize(
            gray, None, 0, 255, cv2.NORM_MINMAX
        )

        heatmap = cv2.applyColorMap(
            normalized, cv2.COLORMAP_JET
        )

        cv2.imwrite(heatmap_path, heatmap)

        threshold = max(
            8.0,
            float(np.percentile(gray, 99.5))
        )

        binary = np.where(
            gray >= threshold, 255, 0
        ).astype(np.uint8)

        kernel = np.ones((3, 3), np.uint8)

        binary = cv2.morphologyEx(
            binary, cv2.MORPH_OPEN, kernel
        )

        binary = cv2.morphologyEx(
            binary, cv2.MORPH_CLOSE, kernel
        )

        count, labels, stats, _ = (
            cv2.connectedComponentsWithStats(binary, 8)
        )

        regions = []

        for i in range(1, count):
            x, y, w, h, area = stats[i]

            if area < 20:
                continue

            region = gray[y:y+h, x:x+w]

            regions.append({
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
                "area": int(area),
                "mean_difference": round(
                    float(np.mean(region)), 2
                )
            })

        regions.sort(
            key=lambda r: r["mean_difference"],
            reverse=True
        )

        overlay = original.copy()

        for r in regions:
            cv2.rectangle(
                overlay,
                (r["x"], r["y"]),
                (r["x"] + r["width"], r["y"] + r["height"]),
                (255, 0, 0),
                2
            )

        cv2.imwrite(
            overlay_path,
            cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
        )

        return {
            "status": "completed",
            "mean_difference": round(mean_difference, 3),
            "maximum_difference": maximum_difference,
            "threshold_used": round(threshold, 2),
            "heatmap_path": os.path.abspath(heatmap_path),
            "overlay_path": os.path.abspath(overlay_path),
            "regions_found": len(regions),
            "suspicious_regions": regions,
            "interpretation": (
                "ELA highlights unusual compression differences. "
                "These are investigation leads, not proof of editing."
            )
        }

    except Exception as error:
        return {
            "status": "error",
            "error": str(error),
            "suspicious_regions": []
        }

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ============================================================
# SPATIAL CLUSTERING
# ============================================================

def get_spatial_cluster(matches, keypoints, radius=45):

    if not matches:
        return []

    source_points = np.array([
        keypoints[m["source_index"]].pt for m in matches
    ], dtype=np.float32)

    best_indices = []

    for point in source_points:

        distances = np.linalg.norm(
            source_points - point, axis=1
        )

        indices = np.where(
            distances <= radius
        )[0].tolist()

        if len(indices) > len(best_indices):
            best_indices = indices

    return [matches[i] for i in best_indices]


# ============================================================
# PATCH SIMILARITY
# ============================================================

def patch_similarity(gray, source, target, patch_size=25):

    half = patch_size // 2

    sx, sy = int(round(source[0])), int(round(source[1]))
    tx, ty = int(round(target[0])), int(round(target[1]))

    height, width = gray.shape

    if (
        sx - half < 0 or sy - half < 0 or
        tx - half < 0 or ty - half < 0 or
        sx + half >= width or sy + half >= height or
        tx + half >= width or ty + half >= height
    ):
        return None

    patch_a = gray[
        sy-half:sy+half+1,
        sx-half:sx+half+1
    ].astype(np.float32)

    patch_b = gray[
        ty-half:ty+half+1,
        tx-half:tx+half+1
    ].astype(np.float32)

    patch_a -= np.mean(patch_a)
    patch_b -= np.mean(patch_b)

    denominator = (
        np.linalg.norm(patch_a) *
        np.linalg.norm(patch_b)
    )

    if denominator < 1e-6:
        return None

    return float(
        np.sum(patch_a * patch_b) / denominator
    )


# ============================================================
# COPY-MOVE DETECTION
# ============================================================

def detect_copy_move(image_path, output_dir):

    os.makedirs(output_dir, exist_ok=True)

    name = os.path.splitext(os.path.basename(image_path))[0]

    visualization_path = os.path.join(
        output_dir, name + "_copy_move.png"
    )

    try:
        image = cv2.imread(image_path)

        if image is None:
            raise ValueError("Could not read image.")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        height, width = gray.shape

        orb = cv2.ORB_create(
            nfeatures=5000,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=15,
            fastThreshold=5
        )

        keypoints, descriptors = orb.detectAndCompute(
            gray, None
        )

        if descriptors is None or len(keypoints) < 10:
            raise ValueError("Not enough visual features.")

        matcher = cv2.BFMatcher(
            cv2.NORM_HAMMING,
            crossCheck=False
        )

        k = min(12, len(descriptors))

        matches = matcher.knnMatch(
            descriptors, descriptors, k=k
        )

        displacement_groups = {}
        accepted_pairs = set()

        bin_size = 10
        minimum_distance = 40
        maximum_descriptor_distance = 35

        for query_index, candidates in enumerate(matches):

            source = keypoints[query_index].pt

            for match in candidates:

                target_index = match.trainIdx

                if target_index == query_index:
                    continue

                target = keypoints[target_index].pt

                dx = target[0] - source[0]
                dy = target[1] - source[1]

                spatial_distance = np.sqrt(dx*dx + dy*dy)

                if spatial_distance < minimum_distance:
                    continue

                if spatial_distance > max(width, height):
                    continue

                if match.distance > maximum_descriptor_distance:
                    continue

                pair = tuple(sorted((query_index, target_index)))

                if pair in accepted_pairs:
                    continue

                accepted_pairs.add(pair)

                dx_bin = int(round(dx / bin_size))
                dy_bin = int(round(dy / bin_size))

                key = (dx_bin, dy_bin)

                if key not in displacement_groups:
                    displacement_groups[key] = []

                displacement_groups[key].append({
                    "source_index": query_index,
                    "target_index": target_index,
                    "distance": float(match.distance),
                    "dx": float(dx),
                    "dy": float(dy)
                })

        if displacement_groups:

            dominant_key = max(
                displacement_groups,
                key=lambda key: len(displacement_groups[key])
            )

            dominant_matches = displacement_groups[dominant_key]

        else:
            dominant_key = (0, 0)
            dominant_matches = []

        # Find a concentrated source region.
        spatial_matches = get_spatial_cluster(
            dominant_matches,
            keypoints,
            radius=45
        )

        source_points = []
        target_points = []

        for match in spatial_matches:

            source_points.append(
                keypoints[match["source_index"]].pt
            )

            target_points.append(
                keypoints[match["target_index"]].pt
            )

        compact_region = False
        patch_scores = []

        source_width = 0
        source_height = 0
        target_width = 0
        target_height = 0

        if len(spatial_matches) >= 8:

            source_array = np.array(source_points)
            target_array = np.array(target_points)

            source_width = (
                np.max(source_array[:, 0]) -
                np.min(source_array[:, 0])
            )

            source_height = (
                np.max(source_array[:, 1]) -
                np.min(source_array[:, 1])
            )

            target_width = (
                np.max(target_array[:, 0]) -
                np.min(target_array[:, 0])
            )

            target_height = (
                np.max(target_array[:, 1]) -
                np.min(target_array[:, 1])
            )

            # Allow narrow horizontal text regions.
            # Do not require every copied region to be tall.

            compact_region = (
                source_width >= 35 and
                target_width >= 35 and
                source_height >= 6 and
                target_height >= 6 and
                source_width >= source_height * 1.5 and
                target_width >= target_height * 1.5
            )

            if compact_region:

                for match in spatial_matches:

                    source = keypoints[
                        match["source_index"]
                    ].pt

                    target = keypoints[
                        match["target_index"]
                    ].pt

                    score = patch_similarity(
                        gray, source, target
                    )

                    if score is not None:
                        patch_scores.append(score)

        # Require strong local pixel-pattern similarity.
        similar_patch_count = sum(
            score >= 0.85 for score in patch_scores
        )

        patch_match_ratio = (
            similar_patch_count / len(patch_scores)
            if patch_scores else 0.0
        )

        # A copied region must pass all verification checks.
        verified = (
            compact_region and
            len(spatial_matches) >= 8 and
            len(patch_scores) >= 12 and
            similar_patch_count >= 12 and
            patch_match_ratio >= 0.35
        )

        match_count = len(spatial_matches)

        if verified and match_count >= 20:
            confidence = 0.80
        elif verified:
            confidence = 0.65
        elif compact_region:
            confidence = 0.30
        else:
            confidence = 0.0

        possible = verified
        strong = verified and match_count >= 12

        # Visualization.
        visualization = image.copy()

        for match in spatial_matches:

            p1 = keypoints[
                match["source_index"]
            ].pt

            p2 = keypoints[
                match["target_index"]
            ].pt

            cv2.line(
                visualization,
                (int(p1[0]), int(p1[1])),
                (int(p2[0]), int(p2[1])),
                (0, 0, 255),
                1
            )

        def draw_bounds(points, color, label):

            if len(points) < 2:
                return

            pts = np.array(points)

            x1 = max(0, int(np.min(pts[:, 0])) - 25)
            y1 = max(0, int(np.min(pts[:, 1])) - 25)

            x2 = min(width - 1, int(np.max(pts[:, 0])) + 25)
            y2 = min(height - 1, int(np.max(pts[:, 1])) + 25)

            cv2.rectangle(
                visualization,
                (x1, y1),
                (x2, y2),
                color,
                3
            )

            cv2.putText(
                visualization,
                label,
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

        if verified:

            draw_bounds(
                source_points,
                (255, 0, 0),
                "SOURCE CANDIDATE"
            )

            draw_bounds(
                target_points,
                (0, 255, 0),
                "DUPLICATE CANDIDATE"
            )

        else:

            cv2.putText(
                visualization,
                "NO VERIFIED COPY-MOVE REGION",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 165, 255),
                2
            )

        cv2.imwrite(visualization_path, visualization)

        if strong:

            interpretation = (
                "A spatially concentrated matching region passed "
                "patch-similarity checks. Possible copy-move "
                "manipulation requires human review."
            )

        elif possible:

            interpretation = (
                "A possible duplicated region passed verification. "
                "Human review is required."
            )

        else:

            interpretation = (
                "No sufficiently verified copy-move region found. "
                "This does not rule out manipulation."
            )

        return {
            "status": "completed",
            "keypoints_found": len(keypoints),
            "candidate_matches": len(accepted_pairs),
            "dominant_group_matches": len(dominant_matches),
            "spatial_cluster_matches": match_count,
            "compact_region": bool(compact_region),
            "source_region_width": round(float(source_width), 2),
            "source_region_height": round(float(source_height), 2),
            "target_region_width": round(float(target_width), 2),
            "target_region_height": round(float(target_height), 2),
            "patches_compared": len(patch_scores),
            "similar_patches": similar_patch_count,
            "patch_match_ratio": round(patch_match_ratio, 3),
            "potential_copy_move": bool(possible),
            "strong_copy_move_signal": bool(strong),
            "confidence_heuristic": confidence,
            "dominant_displacement": {
                "x": int(dominant_key[0] * bin_size),
                "y": int(dominant_key[1] * bin_size)
            },
            "source_points_found": len(source_points),
            "target_points_found": len(target_points),
            "visualization_path": os.path.abspath(
                visualization_path
            ),
            "interpretation": interpretation,
            "limitations": [
                "Repeated text and patterns can still create false matches.",
                "Small copied regions may be missed.",
                "Low-texture images may contain too few features.",
                "Compression and resizing can hide duplicated regions.",
                "Confidence is a heuristic, not a validated probability.",
                "A matching region does not prove intentional manipulation."
            ]
        }

    except Exception as error:

        return {
            "status": "error",
            "error": str(error),
            "potential_copy_move": False,
            "strong_copy_move_signal": False
        }


# ============================================================
# COMPLETE ANALYSIS
# ============================================================

def analyze_image(image_path):

    if not os.path.exists(image_path):
        return {"error": "Image file not found."}

    output_dir = os.path.join(
        "backend", "forensic", "outputs"
    )

    os.makedirs(output_dir, exist_ok=True)

    try:

        image = Image.open(image_path)

        image_info = {
            "format": image.format,
            "width": image.width,
            "height": image.height,
            "mode": image.mode
        }

        sha256 = calculate_sha256(image_path)

        metadata = extract_metadata(image)

        ela = perform_ela(
            image, image_path, output_dir
        )

        copy_move = detect_copy_move(
            image_path, output_dir
        )

        regions = ela.get("suspicious_regions", [])

        findings = [
            "SHA-256 fingerprint generated.",
            "Image dimensions and metadata examined.",
            "JPEG Error Level Analysis performed.",
            "Copy-move feature matching and patch verification performed."
        ]

        if regions:
            findings.append(
                f"{len(regions)} unusual compression regions identified."
            )

        if copy_move.get("potential_copy_move"):
            findings.append(
                "Possible verified copy-move pattern identified."
            )

        if copy_move.get("strong_copy_move_signal"):
            findings.append(
                "Strong copy-move verification signal identified."
            )

        if copy_move.get("strong_copy_move_signal"):
            verdict = "Suspicious"

        elif (
            copy_move.get("potential_copy_move")
            and len(regions) >= 3
        ):
            verdict = "Suspicious"

        else:
            verdict = "Inconclusive"

        return {
            "file_name": os.path.basename(image_path),
            "sha256": sha256,
            "image_info": image_info,
            "metadata": metadata,
            "ela": ela,
            "suspicious_regions": regions,
            "copy_move_analysis": copy_move,
            "findings": findings,
            "verdict": verdict,
            "limitations": [
                "ELA differences do not prove manipulation.",
                "Missing EXIF data does not prove an image is fake.",
                "SHA-256 identifies a file, not its authenticity.",
                "Localized regions require human review.",
                "Copy-move matching is a forensic signal, not absolute proof."
            ]
        }

    except Exception as error:
        return {"error": str(error)}


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:
        print("Usage: python detector.py <image_path>")
        raise SystemExit(1)

    print(json.dumps(
        analyze_image(sys.argv[1]),
        indent=4
    ))
