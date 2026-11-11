
import uuid
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from PIL import Image, UnidentifiedImageError

from forensic.detector import analyze_image


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "backend" / "uploads"
OUTPUT_DIR = BASE_DIR / "backend" / "forensic" / "outputs"

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE


# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "application": "TRUTHSCAN AI",
        "module": "Forensic Analysis API",
        "status": "running",
        "message": "Forensic analysis service is ready."
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "forensic_engine": "available"
    })


# --------------------------------------------------
# FORENSIC IMAGE ANALYSIS
# --------------------------------------------------

@app.route("/api/forensic/analyze", methods=["POST"])
def forensic_analyze():

    if "image" not in request.files:
        return jsonify({
            "success": False,
            "error": "No image uploaded. Use the field name 'image'."
        }), 400

    uploaded_file = request.files["image"]

    if not uploaded_file.filename:
        return jsonify({
            "success": False,
            "error": "Please select an image."
        }), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify({
            "success": False,
            "error": "Unsupported file type. Use JPG, JPEG, PNG or WEBP."
        }), 400

    request_id = str(uuid.uuid4())

    safe_name = secure_filename(uploaded_file.filename)
    extension = safe_name.rsplit(".", 1)[1].lower()

    saved_filename = f"{request_id}.{extension}"
    saved_path = UPLOAD_DIR / saved_filename

    try:
        uploaded_file.save(saved_path)

        # Verify actual image content, not just its extension.
        with Image.open(saved_path) as image:
            image.verify()

        # Run the existing forensic engine.
        result = analyze_image(str(saved_path))

        if not isinstance(result, dict) or "error" in result:
            saved_path.unlink(missing_ok=True)
            return jsonify({
                "success": False,
                "error": "Forensic analysis could not be completed."
            }), 422

        # Generate visualization URLs.
        copy_move_name = f"{request_id}_copy_move.png"
        ela_name = f"{request_id}_ela.png"
        regions_name = f"{request_id}_regions.png"

        copy_move_path = OUTPUT_DIR / copy_move_name
        ela_path = OUTPUT_DIR / ela_name
        regions_path = OUTPUT_DIR / regions_name

        # Remove internal computer paths from the response.
        copy_move_data = result.get("copy_move_analysis", {})
        copy_move_data.pop("visualization_path", None)

        ela_data = result.get("ela", {})
        ela_data.pop("heatmap_path", None)
        ela_data.pop("overlay_path", None)

        # Provide frontend-friendly visualization URLs.
        result["visualizations"] = {
            "copy_move": (
                f"/api/forensic/outputs/{copy_move_name}"
                if copy_move_path.is_file() else None
            ),
            "ela": (
                f"/api/forensic/outputs/{ela_name}"
                if ela_path.is_file() else None
            ),
            "regions": (
                f"/api/forensic/outputs/{regions_name}"
                if regions_path.is_file() else None
            )
        }

        return jsonify({
            "success": True,
            "request_id": request_id,
            "analysis": result
        }), 200

    except (UnidentifiedImageError, OSError):
        saved_path.unlink(missing_ok=True)

        return jsonify({
            "success": False,
            "error": "The uploaded file is not a valid supported image."
        }), 400

    except Exception:
        app.logger.exception("Forensic analysis failed")
        saved_path.unlink(missing_ok=True)

        return jsonify({
            "success": False,
            "error": "An internal error occurred during forensic analysis."
        }), 500


# --------------------------------------------------
# VISUALIZATION ACCESS
# --------------------------------------------------

@app.route("/api/forensic/outputs/<filename>", methods=["GET"])
def get_output(filename):

    if not filename.endswith(".png"):
        return jsonify({
            "success": False,
            "error": "Invalid visualization file."
        }), 400

    return send_from_directory(
        str(OUTPUT_DIR),
        filename
    )


# --------------------------------------------------
# ERROR HANDLING
# --------------------------------------------------

@app.errorhandler(RequestEntityTooLarge)
def file_too_large(error):
    return jsonify({
        "success": False,
        "error": "Image exceeds the 10 MB upload limit."
    }), 413


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "API endpoint not found."
    }), 404


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
