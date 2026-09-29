import os
import subprocess
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_file, render_template

import cv_data

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "rendercv_output"

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html", themes=cv_data.AVAILABLE_THEMES)


@app.get("/api/cv")
def get_cv():
    return jsonify(cv_data.load_cv())


@app.post("/api/cv")
def post_cv():
    data = request.get_json(force=True)
    cv_data.save_cv(data)
    return jsonify({"ok": True})


@app.post("/api/render")
def render_cv():
    data = request.get_json(force=True)
    cv_data.save_cv(data)

    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, "-m", "rendercv", "render", "cv.yaml"],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    pdf_path = OUTPUT_DIR / "cv.pdf"
    png_path = OUTPUT_DIR / "cv_1.png"
    pdf_path = pdf_path if pdf_path.exists() else None
    png_path = png_path if png_path.exists() else None

    return jsonify(
        {
            "ok": result.returncode == 0 and pdf_path is not None,
            "log": (result.stdout or "") + (result.stderr or ""),
            "pdf_ready": pdf_path is not None,
            "preview_ready": png_path is not None,
        }
    )


ALLOWED_PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@app.post("/api/photo")
def upload_photo():
    file = request.files.get("photo")
    if not file or not file.filename:
        return jsonify({"error": "No file provided"}), 400
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_PHOTO_EXTENSIONS:
        return jsonify({"error": "Only .jpg, .jpeg, .png files are supported"}), 400

    relative_path = cv_data.save_photo(file.filename, file.read())
    data = cv_data.load_cv()
    data["photo"] = relative_path
    cv_data.save_cv(data)
    return jsonify({"ok": True, "photo": relative_path})


@app.delete("/api/photo")
def delete_photo():
    photo_path = cv_data.current_photo_path()
    if photo_path:
        photo_path.unlink()
    data = cv_data.load_cv()
    data["photo"] = ""
    cv_data.save_cv(data)
    return jsonify({"ok": True})


@app.get("/api/photo")
def get_photo():
    photo_path = cv_data.current_photo_path()
    if not photo_path:
        return jsonify({"error": "No photo uploaded"}), 404
    return send_file(photo_path)


@app.get("/api/pdf")
def get_pdf():
    pdf_path = OUTPUT_DIR / "cv.pdf"
    if not pdf_path.exists():
        return jsonify({"error": "No rendered PDF yet"}), 404
    return send_file(pdf_path, mimetype="application/pdf")


@app.get("/api/preview/<int:page>")
def get_preview(page: int):
    png_path = OUTPUT_DIR / f"cv_{page}.png"
    if not png_path.exists():
        return jsonify({"error": "No preview yet"}), 404
    return send_file(png_path, mimetype="image/png")


if __name__ == "__main__":
    # use_reloader=False: the stat reloader re-execs this script on every file
    # change and was observed alternating between the venv and base Anaconda
    # interpreters on this machine, leaving orphaned processes that hold file
    # locks on rendercv_output/. Restart the server manually after edits.
    app.run(debug=True, port=5055, use_reloader=False)
