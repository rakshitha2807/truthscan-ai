import json
from datetime import datetime
"""
=========================================================
TRUTHSCAN AI - EVIDENCE CONSISTENCY GRAPH
=========================================================

Developer: Friend 2

FEATURES:
1. OCR text extraction.
2. Image preprocessing and enhancement.
3. Original and enhanced OCR comparison.
4. Payment amount extraction.
5. Rupee symbol OCR correction candidate detection.
6. Date and transaction ID extraction.
7. Payment status extraction.
8. Cross-screenshot comparison.
9. Contradiction detection.
10. Evidence graph generation.

IMPORTANT:
A contradiction is an investigation clue, NOT proof of fraud.
OCR results must be verified against the original screenshot.
=========================================================
"""

import re
from pathlib import Path

import cv2
from rapidocr_onnxruntime import RapidOCR


# =========================================================
# STEP 1: INITIALIZE OCR ENGINE
# =========================================================

ocr_engine = RapidOCR()


# =========================================================
# STEP 2: IMAGE PREPROCESSING
# =========================================================

def preprocess_image(image_path):

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(f"Cannot read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    enlarged = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(enlarged)

    return enhanced


# =========================================================
# STEP 3: OCR TEXT EXTRACTION
# =========================================================

def extract_text(image_path, image=None):

    image_path = Path(image_path)

    if image is None:

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        ocr_input = str(image_path)

    else:
        ocr_input = image

    results, _ = ocr_engine(ocr_input)

    extracted_lines = []
    confidence_scores = []
    detections = []

    if results:

        for item in results:

            text = item[1]
            confidence = float(item[2])
            bbox = item[0]

            extracted_lines.append(text)
            confidence_scores.append(confidence)

            detections.append({
                "text": text,
                "confidence": confidence,
                "bbox": bbox
            })

            print("\nDetected OCR text:", text)
            print("Confidence:", confidence)
            print("Bounding box:", bbox)

    full_text = " ".join(extracted_lines)

    average_confidence = (
        sum(confidence_scores) / len(confidence_scores)
        if confidence_scores else 0.0
    )

    return {
        "text": full_text,
        "ocr_confidence": round(average_confidence, 3),
        "detections": detections
    }


# =========================================================
# STEP 4: COMPARE ORIGINAL AND ENHANCED OCR
# =========================================================

def compare_ocr_versions(image_path):

    original = extract_text(image_path)

    enhanced_image = preprocess_image(image_path)

    processed = extract_text(
        image_path,
        image=enhanced_image
    )

    original_normalized = " ".join(
        original["text"].lower().split()
    )

    processed_normalized = " ".join(
        processed["text"].lower().split()
    )

    results_agree = (
        original_normalized == processed_normalized
    )

    return {
        "original_text": original["text"],
        "original_confidence": original["ocr_confidence"],
        "original_detections": original["detections"],

        "processed_text": processed["text"],
        "processed_confidence": processed["ocr_confidence"],
        "processed_detections": processed["detections"],

        "results_agree": results_agree
    }


# =========================================================
# STEP 5: EXTRACT PAYMENT AMOUNT FROM OCR CROP
# =========================================================


def extract_amount_from_crop(image, bbox):

    """
    Re-recognize the numeric portion of the payment amount.

    Tries grayscale, inverted grayscale and thresholded images.
    """

    try:

        height, width = image.shape[:2]

        xs = [int(point[0]) for point in bbox]
        ys = [int(point[1]) for point in bbox]

        x_min = min(xs)
        x_max = max(xs)
        y_min = min(ys)
        y_max = max(ys)

        box_width = x_max - x_min
        box_height = y_max - y_min

        # Exclude the rupee symbol, retaining the first digit.
        x1 = max(0, int(x_min + box_width * 0.14))
        x2 = min(width, x_max + int(box_width * 0.05))

        y1 = max(0, int(y_min - box_height * 0.15))
        y2 = min(height, int(y_max + box_height * 0.15))

        crop = image[y1:y2, x1:x2]

        if crop.size == 0:
            return None

        gray = cv2.cvtColor(
            crop,
            cv2.COLOR_BGR2GRAY
        )

        enlarged = cv2.resize(
            gray,
            None,
            fx=3,
            fy=3,
            interpolation=cv2.INTER_CUBIC
        )

        _, thresholded = cv2.threshold(
            enlarged,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        inverted = cv2.bitwise_not(thresholded)

        variants = [
            enlarged,
            thresholded,
            inverted
        ]

        for index, variant in enumerate(variants):

            # Add white padding around the text.
            padded = cv2.copyMakeBorder(
                variant,
                40, 40, 40, 40,
                cv2.BORDER_CONSTANT,
                value=255
            )

            results, _ = ocr_engine(padded)

            detected_text = ""

            if results:

                detected_text = " ".join(
                    item[1] for item in results
                )

            print(
                f"Amount crop attempt {index + 1}:",
                detected_text
            )

            amounts = extract_numeric_amounts(
                detected_text
            )

            if len(amounts) == 1:

                return amounts[0]

        return None

    except Exception as error:

        print("Crop OCR error:", error)

        return None



# =========================================================
# STEP 6: EXTRACT NUMERIC AMOUNTS
# =========================================================


def extract_numeric_amounts(text):

    """
    Extract only comma-formatted payment amounts.

    This prevents date and time values such as
    1Jun2024 and 11:50 from becoming amounts.
    """

    amount_pattern = (
        r"(?<![\w:])"
        r"("
        r"\d{1,2}(?:,\d{2})+,\d{3}"
        r"|"
        r"\d{1,3}(?:,\d{3})+"
        r")"
        r"(?![\d,:])"
    )

    raw_amounts = re.findall(
        amount_pattern,
        text
    )

    return sorted({
        float(value.replace(",", ""))
        for value in raw_amounts
    })



# =========================================================
# STEP 7: EXTRACT PAYMENT INFORMATION
# =========================================================

def extract_fields(text):

    normalized_text = text.lower()

    # -----------------------------------------------
    # 1. EXTRACT AMOUNTS
    # -----------------------------------------------

    amounts = extract_numeric_amounts(text)

    # -----------------------------------------------
    # 2. EXTRACT DATES
    # -----------------------------------------------

    date_patterns = [

        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

        r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b",

        r"\b\d{1,2}[A-Za-z]{3,9}\d{4}\b"

    ]

    dates = []

    for pattern in date_patterns:

        dates.extend(
            re.findall(
                pattern,
                text,
                flags=re.IGNORECASE
            )
        )

    dates = sorted(set(dates))

    # -----------------------------------------------
    # 3. EXTRACT TRANSACTION IDS
    # -----------------------------------------------

    id_pattern = (
        r"(?:utr|transaction\s*(?:id|ref(?:erence)?|no\.?)|"
        r"reference\s*(?:no|number|id)?)"
        r"\s*[:#\-]?\s*([a-z0-9]{6,})"
    )

    transaction_ids = sorted({

        value.upper()

        for value in re.findall(
            id_pattern,
            text,
            flags=re.IGNORECASE
        )

    })

    # -----------------------------------------------
    # 4. EXTRACT PAYMENT STATUS
    # -----------------------------------------------

    status_keywords = [
        "successful",
        "success",
        "completed",
        "pending",
        "failed",
        "declined"
    ]

    statuses = []

    for status in status_keywords:

        if status in normalized_text:
            statuses.append(status)

    return {
        "amounts": amounts,
        "dates": dates,
        "transaction_ids": transaction_ids,
        "statuses": sorted(set(statuses))
    }


# =========================================================
# STEP 8: ANALYZE ONE SCREENSHOT
# =========================================================

def analyze_evidence(image_path):

    ocr_comparison = compare_ocr_versions(image_path)

    original_text = ocr_comparison["original_text"]

    # Extract normal payment fields.
    fields = extract_fields(original_text)
    # Extract amounts only from individual OCR detections.
# This prevents dates and times from being counted.

    line_amounts = []

    for detection in ocr_comparison["original_detections"]:

        detected_text = detection["text"]

        line_amounts.extend(
            extract_numeric_amounts(detected_text)
        )

    fields["amounts"] = sorted(set(line_amounts))
    processed_fields = extract_fields(
        ocr_comparison["processed_text"]
    )

    # -------------------------------------------------
    # SPECIAL AMOUNT VERIFICATION
    # -------------------------------------------------

    image = cv2.imread(str(image_path))

    amount_correction = None
    amount_review_required = False

    if image is not None:

        for detection in ocr_comparison["original_detections"]:

            detected_text = detection["text"].strip()

            # Apply the special crop only when OCR appears
            # to have interpreted a currency symbol as 7.
            #
            # Example:
            # OCR: 75,000
            # Actual screenshot: ₹5,000

            if re.fullmatch(
                r"7\d,\d{3}",
                detected_text
            ):

                print("\nPossible rupee symbol confusion detected.")

                cropped_amount = extract_amount_from_crop(
                    image,
                    detection["bbox"]
                )

                if cropped_amount is not None:

                    original_amounts = extract_numeric_amounts(
                        detected_text
                    )

                    if (
                        len(original_amounts) == 1
                        and cropped_amount != original_amounts[0]
                    ):

                        amount_correction = {
                            "original_ocr_amount": original_amounts[0],
                            "cropped_ocr_candidate": cropped_amount
                        }

                        # Use the cropped OCR candidate, but
                        # explicitly flag it for visual review.
                        fields["amounts"] = [cropped_amount]

                        amount_review_required = True

                        print(
                            "Amount correction candidate:",
                            amount_correction
                        )
                else:
                    amount_review_required = True
                    print("WARNING: Amount could not be independently verified.")
                break
            

    # -------------------------------------------------
    # COMPARE AMOUNTS
    # -------------------------------------------------

    amount_disagreement = (
        fields["amounts"] != processed_fields["amounts"]
    )

    return {

        "file": Path(image_path).name,

        "ocr_text": original_text,

        "ocr_confidence": (
            ocr_comparison["original_confidence"]
        ),

        "processed_text": (
            ocr_comparison["processed_text"]
        ),

        "processed_confidence": (
            ocr_comparison["processed_confidence"]
        ),

        "ocr_versions_agree": (
            ocr_comparison["results_agree"]
        ),

        "amount_disagreement": amount_disagreement,

        "amount_review_required": amount_review_required,

        "amount_correction": amount_correction,

        "fields": fields,

        "processed_fields": processed_fields

    }


# =========================================================
# STEP 9: COMPARE MULTIPLE SCREENSHOTS
# =========================================================

def compare_evidence(files):

    documents = []

    contradictions = []

    # Analyze all screenshots.
    for image_path in files:

        result = analyze_evidence(image_path)

        documents.append(result)

    # Compare screenshots pair by pair.
    for i in range(len(documents)):

        for j in range(i + 1, len(documents)):

            first = documents[i]
            second = documents[j]

            first_fields = first["fields"]
            second_fields = second["fields"]

            # -----------------------------------------
            # COMPARE PAYMENT AMOUNTS
            # -----------------------------------------

            if (
                len(first_fields["amounts"]) == 1
                and len(second_fields["amounts"]) == 1
            ):

                amount1 = first_fields["amounts"][0]
                amount2 = second_fields["amounts"][0]

                if amount1 != amount2:

                    contradictions.append({

                        "type": "AMOUNT_MISMATCH",

                        "field": "amount",

                        "file1": first["file"],

                        "file2": second["file"],

                        "value1": amount1,

                        "value2": amount2,

                        "message": (
                            "Different payment amounts "
                            "were extracted."
                        )

                    })

            # -----------------------------------------
            # COMPARE TRANSACTION IDS
            # -----------------------------------------

            if (
                len(first_fields["transaction_ids"]) == 1
                and len(second_fields["transaction_ids"]) == 1
            ):

                id1 = first_fields["transaction_ids"][0]
                id2 = second_fields["transaction_ids"][0]

                if id1 != id2:

                    contradictions.append({

                        "type": "TRANSACTION_ID_MISMATCH",

                        "field": "transaction_id",

                        "file1": first["file"],

                        "file2": second["file"],

                        "value1": id1,

                        "value2": id2,

                        "message": (
                            "Transaction IDs do not match."
                        )

                    })

            # -----------------------------------------
            # COMPARE DATES
            # -----------------------------------------

            if (
                len(first_fields["dates"]) == 1
                and len(second_fields["dates"]) == 1
            ):

                date1 = first_fields["dates"][0]
                date2 = second_fields["dates"][0]

                if date1 != date2:

                    contradictions.append({

                        "type": "DATE_MISMATCH",

                        "field": "date",

                        "file1": first["file"],

                        "file2": second["file"],

                        "value1": date1,

                        "value2": date2,

                        "message": (
                            "Different dates were extracted."
                        )

                    })

            # -----------------------------------------
            # COMPARE PAYMENT STATUSES
            # -----------------------------------------

            if (
                len(first_fields["statuses"]) == 1
                and len(second_fields["statuses"]) == 1
            ):

                status1 = first_fields["statuses"][0]
                status2 = second_fields["statuses"][0]

                if status1 != status2:

                    contradictions.append({

                        "type": "STATUS_MISMATCH",

                        "field": "payment_status",

                        "file1": first["file"],

                        "file2": second["file"],

                        "value1": status1,

                        "value2": status2,

                        "message": (
                            "Payment statuses are inconsistent."
                        )

                    })

    # =====================================================
    # STEP 10: GENERATE EVIDENCE GRAPH
    # =====================================================

    nodes = []
    edges = []

    # Create document nodes.
    for index, document in enumerate(documents):

        nodes.append({

            "id": f"doc_{index + 1}",

            "label": document["file"],

            "type": "document"

        })

    # Create contradiction nodes.
    for index, issue in enumerate(contradictions):

        issue_id = f"issue_{index + 1}"

        nodes.append({

            "id": issue_id,

            "label": issue["type"],

            "type": "contradiction"

        })

        # Connect related documents.
        for doc_index, document in enumerate(documents):

            if document["file"] in [
                issue["file1"],
                issue["file2"]
            ]:

                edges.append({

                    "source": f"doc_{doc_index + 1}",

                    "target": issue_id

                })

    # =====================================================
    # STEP 11: GENERATE FINAL SUMMARY
    # =====================================================

    uncertain_documents = sum(

        1 for document in documents

        if (
            document["amount_disagreement"]
            or document["amount_review_required"]
        )

    )

    summary = {

        "total_documents": len(documents),

        "total_contradictions": len(contradictions),

        "ocr_uncertain_documents": uncertain_documents,

        "status": (

            "REVIEW_REQUIRED"

            if contradictions or uncertain_documents

            else "NO_CONTRADICTIONS_FOUND"

        )

    }

    return {

        "documents": documents,

        "contradictions": contradictions,

        "summary": summary,

        "graph": {

            "nodes": nodes,

            "edges": edges

        }

    }


# =========================================================
# STEP 12: RUN COMPLETE ANALYSIS
# =========================================================

if __name__ == "__main__":

    print("\n===================================")
    print(" TRUTHSCAN AI - EVIDENCE ANALYSIS")
    print("===================================\n")

    # Locate project root.
    project_root = Path(__file__).resolve().parents[2]

    # Locate sample screenshots.
    sample_folder = project_root / "sample_evidence"

    # Find supported image files.
    image_files = []

    for extension in ["*.png", "*.jpg", "*.jpeg"]:

        image_files.extend(
            sample_folder.glob(extension)
        )

    image_files = sorted(image_files)

    if not image_files:

        print("No sample screenshots found!")

    else:

        # ---------------------------------------------
        # ANALYZE EACH SCREENSHOT
        # ---------------------------------------------

        for image_path in image_files:

            print(f"\nAnalyzing: {image_path.name}")

            try:

                result = analyze_evidence(image_path)

                print("\nOriginal OCR:")
                print(result["ocr_text"])

                print("\nEnhanced OCR:")
                print(result["processed_text"])

                print("\nExtracted fields:")
                print(result["fields"])

                print(
                    "\nOCR versions agree:",
                    result["ocr_versions_agree"]
                )

                print(
                    "Amount disagreement:",
                    result["amount_disagreement"]
                )

                print(
                    "Amount review required:",
                    result["amount_review_required"]
                )

                if result["amount_correction"]:

                    print(
                        "Amount correction candidate:",
                        result["amount_correction"]
                    )

            except Exception as error:

                print(
                    f"Error analyzing {image_path.name}: {error}"
                )

        # ---------------------------------------------
        # CROSS-SCREENSHOT COMPARISON
        # ---------------------------------------------

        print("\n===================================")
        print(" CROSS-SCREENSHOT COMPARISON")
        print("===================================")

        try:

            final_result = compare_evidence(image_files)
            
            # =============================================
            # SAVE EVIDENCE ANALYSIS REPORT
            # =============================================

            report_folder = project_root / "reports"

            report_folder.mkdir(
                parents=True,
                exist_ok=True
            )

            report = {
                "project": "TruthScan AI",

                "generated_at": datetime.now().isoformat(),

                "summary": final_result["summary"],

                "documents": final_result["documents"],

                "contradictions": final_result["contradictions"],

                "evidence_graph": final_result["graph"]
            }

            report_path = report_folder / "evidence_report.json"

            with open(report_path, "w", encoding="utf-8") as file:

                json.dump(
                    report,
                    file,
                    indent=4,
                    ensure_ascii=False,
                    default=lambda value: (
                        value.item()
                        if hasattr(value, "item")
                        else str(value)
                    )
                )

            print("\nEVIDENCE REPORT SAVED SUCCESSFULLY")

            print("Report location:", report_path)

            print("\nSUMMARY:")
            print(final_result["summary"])

            print("\nCONTRADICTIONS:")

            for issue in final_result["contradictions"]:

                print(issue)

            print("\nEVIDENCE GRAPH:")
            print(final_result["graph"])

        except Exception as error:

            print(f"Comparison error: {error}")

    # ---------------------------------------------
    # IMAGE QUALITY INFORMATION
    # ---------------------------------------------

    print("\n===================================")
    print(" EVIDENCE ANALYSIS COMPLETED")
    print("===================================")

    test_image = sample_folder / "payment2.png"

    image = cv2.imread(str(test_image))

    if image is not None:

        height, width = image.shape[:2]

        print("\nIMAGE QUALITY INFORMATION")

        print("Width:", width)

        print("Height:", height)

        print("Image size (bytes):", test_image.stat().st_size)

    else:

        print("\nCould not read payment2.png")
