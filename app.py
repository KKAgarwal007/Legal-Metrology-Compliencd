"""
Legal Metrology Compliance Checker & Enforcement System.
AI-Powered Product Verification with PaddleOCR, RAG Legal Retrieval & Supabase.
"""

import os
import json
import uuid
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    send_from_directory, jsonify, abort
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from werkzeug.utils import secure_filename

from models import db, User, Product, Scan, Violation
import ocr_engine
import rule_engine
import rag_engine
import report_generator
import supabase_client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
CROPS_DIR = os.path.join(UPLOAD_DIR, "crops")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CROPS_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("APP_SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'compliance.db')}"
)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload cap

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.context_processor
def inject_global_status():
    """Inject Supabase connection status across all rendered templates."""
    return {
        "supabase_status": supabase_client.get_supabase_status(),
        "now_year": datetime.utcnow().year,
    }


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def dashboard():
    total_scans = Scan.query.count()
    compliant = Scan.query.filter_by(status="compliant").count()
    non_compliant = Scan.query.filter_by(status="non_compliant").count()
    review = Scan.query.filter_by(status="review").count()

    recent_scans = Scan.query.order_by(Scan.created_at.desc()).limit(10).all()

    # Violation breakdown
    freq = {}
    for v in Violation.query.all():
        freq[v.field] = freq.get(v.field, 0) + 1
    top_violations = sorted(freq.items(), key=lambda x: -x[1])[:6]

    return render_template(
        "dashboard.html",
        total_scans=total_scans,
        compliant=compliant,
        non_compliant=non_compliant,
        review=review,
        recent_scans=recent_scans,
        top_violations=top_violations,
    )


# ---------------------------------------------------------------------------
# Upload & Scan Execution Pipeline
# ---------------------------------------------------------------------------
@app.route("/scan/new", methods=["GET", "POST"])
@login_required
def new_scan():
    if request.method == "GET":
        return render_template("upload.html")

    file = request.files.get("image")
    product_name = request.form.get("product_name", "").strip()
    brand = request.form.get("brand", "").strip()
    category = request.form.get("category", "").strip() or "other"
    is_imported = request.form.get("is_imported") == "on"
    px_per_mm_raw = request.form.get("px_per_mm", "").strip()
    px_per_mm = float(px_per_mm_raw) if px_per_mm_raw else None

    if not file or file.filename == "":
        flash("Please choose a product image to upload.", "error")
        return redirect(url_for("new_scan"))
    if not allowed_file(file.filename):
        flash("Unsupported file format. Please upload JPG, PNG, or WEBP.", "error")
        return redirect(url_for("new_scan"))
    if not product_name:
        flash("Product name is mandatory for inspection record.", "error")
        return redirect(url_for("new_scan"))

    # Step 1: Save image
    ext = file.filename.rsplit(".", 1)[1].lower()
    fname = f"{uuid.uuid4().hex}.{ext}"
    image_path = os.path.join(UPLOAD_DIR, fname)
    file.save(image_path)

    # Step 2 & 3: Image Processing & PaddleOCR
    try:
        analysis = ocr_engine.analyze_image(image_path, px_per_mm=px_per_mm)
    except Exception as exc:
        app.logger.exception("Computer Vision / OCR analysis failed: %s", exc)
        flash(f"Computer Vision / OCR analysis failed: {exc}", "error")
        return redirect(url_for("new_scan"))

    ocr_text = analysis["raw_text"] or ""
    ocr_words = analysis.get("words", [])
    barcode_info = analysis.get("barcode_info", {})
    image_dims = analysis.get("image_dimensions", [800, 800])

    # Step 4 & 5: Structured Information Extraction + RAG Legal Basis Retrieval
    product_meta = {"name": product_name, "brand": brand, "category": category}
    extracted_fields = rule_engine.extract_structured_fields(
        raw_ocr_text=ocr_text,
        ocr_words=ocr_words,
        product_metadata=product_meta,
        image_path=image_path,
        crop_dir=CROPS_DIR,
        is_imported=is_imported,
    )

    # Step 6: Font Sizing & Overall Compliance Scoring
    required_font_mm = rule_engine.min_font_requirement_mm(analysis.get("pdp_area_cm2"))
    detected_font_mm = analysis.get("min_declaration_font_mm")
    font_ok = (detected_font_mm is None) or (detected_font_mm >= required_font_mm)

    compliance_result = rule_engine.evaluate_overall_compliance(
        extracted_fields=extracted_fields,
        font_ok=font_ok,
        detected_font_mm=detected_font_mm,
        required_font_mm=required_font_mm,
    )

    # Step 7: Persist Product & Scan in Local Database
    product = Product.query.filter_by(name=product_name, brand=brand).first()
    if not product:
        product = Product(name=product_name, brand=brand, category=category)
        db.session.add(product)
        db.session.flush()

    extracted_payload = {
        "extracted_fields": extracted_fields,
        "compliance_summary": compliance_result,
        "barcode_info": barcode_info,
        "image_dimensions": image_dims,
        "pdp_area_cm2": analysis.get("pdp_area_cm2"),
        "detected_font_mm": detected_font_mm,
        "required_font_mm": required_font_mm,
        "font_calibrated": analysis.get("font_measurement_calibrated", False),
    }

    scan = Scan(
        product_id=product.id,
        inspector_id=current_user.id,
        image_path=image_path,
        raw_ocr_text=ocr_text,
        extracted_fields_json=json.dumps(extracted_payload),
        min_font_height_mm=detected_font_mm,
        compliance_score=compliance_result["score"],
        status=compliance_result["status"],
    )
    db.session.add(scan)
    db.session.flush()

    for v in compliance_result["violations"]:
        db.session.add(Violation(
            scan_id=scan.id,
            rule_code=v["rule_code"],
            field=v["field"],
            description=v["description"],
            severity=v["severity"],
        ))
    db.session.commit()

    # Step 8: Persist to Supabase Cloud Database (Dual-mode)
    try:
        supabase_pid = supabase_client.save_product_to_supabase(product_name, brand, category)
        supabase_client.save_scan_to_supabase(
            product_id=supabase_pid,
            inspector_username=current_user.username,
            image_url=url_for("serve_upload", filename=fname, _external=True),
            raw_ocr_text=ocr_text,
            extracted_fields_json=extracted_payload,
            min_font_height_mm=detected_font_mm,
            compliance_score=compliance_result["score"],
            status=compliance_result["status"],
            violations=compliance_result["violations"],
        )
    except Exception as exc:
        app.logger.warning(f"Supabase persistence notice: {exc}")

    # Step 9: Generate PDF Report
    report_fname = f"report_{scan.id}.pdf"
    report_path = os.path.join(REPORT_DIR, report_fname)
    try:
        report_generator.build_report(scan, product, scan.violations, report_path)
        scan.report_path = report_path
        db.session.commit()
    except Exception as exc:
        app.logger.warning(f"PDF report generation notice: {exc}")

    return redirect(url_for("scan_detail", scan_id=scan.id))


# ---------------------------------------------------------------------------
# File Serving
# ---------------------------------------------------------------------------
@app.route("/uploads/<path:filename>")
@login_required
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/uploads/crops/<path:filename>")
@login_required
def serve_crop(filename):
    return send_from_directory(CROPS_DIR, filename)


# ---------------------------------------------------------------------------
# Scan Detail & Report
# ---------------------------------------------------------------------------
@app.route("/scan/<int:scan_id>")
@login_required
def scan_detail(scan_id):
    scan = db.session.get(Scan, scan_id) or abort(404)
    data = json.loads(scan.extracted_fields_json or "{}")

    extracted_fields = data.get("extracted_fields", {})
    compliance_summary = data.get("compliance_summary", {})
    barcode_info = data.get("barcode_info", {})
    image_dims = data.get("image_dimensions", [800, 800])

    # Pre-select first available field for initial evidence preview
    active_field_key = "mrp"
    if active_field_key not in extracted_fields and extracted_fields:
        active_field_key = next(iter(extracted_fields))

    active_field_data = extracted_fields.get(active_field_key, {})

    return render_template(
        "scan_detail.html",
        scan=scan,
        product=scan.product,
        extracted_fields=extracted_fields,
        compliance_summary=compliance_summary,
        barcode_info=barcode_info,
        image_dims=image_dims,
        active_field_key=active_field_key,
        active_field_data=active_field_data,
        violations=scan.violations,
        data=data,
    )


@app.route("/scan/<int:scan_id>/report.pdf")
@login_required
def download_report(scan_id):
    scan = db.session.get(Scan, scan_id) or abort(404)
    if not scan.report_path or not os.path.exists(scan.report_path):
        abort(404)
    directory, fname = os.path.split(scan.report_path)
    return send_from_directory(
        directory, fname, as_attachment=True,
        download_name=f"compliance_report_{scan_id}.pdf"
    )


@app.route("/repository")
@login_required
def repository():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    query = Scan.query.join(Product)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Product.name.ilike(like)) | (Product.brand.ilike(like))
        )
    if status:
        query = query.filter(Scan.status == status)

    scans = query.order_by(Scan.created_at.desc()).limit(200).all()
    return render_template("repository.html", scans=scans, q=q, status=status)


# ---------------------------------------------------------------------------
# RAG Search & Supabase Status API
# ---------------------------------------------------------------------------
@app.route("/api/rag/query", methods=["GET", "POST"])
@login_required
def api_rag_query():
    """Query the Legal Metrology RAG vector store for official clauses and provisions."""
    if request.method == "POST":
        payload = request.get_json() or {}
        query = payload.get("query", "").strip()
    else:
        query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"results": []})

    results = rag_engine.query_rag(query, top_k=4)
    return jsonify({"query": query, "results": results})


@app.route("/api/supabase/status")
@login_required
def api_supabase_status():
    """Return Supabase connection health check."""
    return jsonify(supabase_client.get_supabase_status())


# ---------------------------------------------------------------------------
# CLI Bootstrap
# ---------------------------------------------------------------------------
def init_db_and_seed():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", role="admin")
            admin.set_password("ChangeMe123!")
            db.session.add(admin)
        if not User.query.filter_by(username="inspector1").first():
            insp = User(username="inspector1", role="inspector")
            insp.set_password("ChangeMe123!")
            db.session.add(insp)
        db.session.commit()
    print("Database initialised. Default users:")
    print("  admin / ChangeMe123!   (role: admin)")
    print("  inspector1 / ChangeMe123! (role: inspector)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "initdb":
        init_db_and_seed()
    else:
        app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
