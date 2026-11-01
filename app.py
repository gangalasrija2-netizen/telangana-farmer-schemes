import json, os, re, secrets
from datetime import datetime
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-this-secret-before-deployment")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///farmer_schemes.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
db = SQLAlchemy(app)

@app.before_request
def csrf_protect():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    if request.method == "POST":
        submitted = request.form.get("_csrf_token", "")
        expected = session.get("_csrf_token", "")
        import hmac
        if not submitted or not hmac.compare_digest(submitted, expected):
            abort(400, description="Invalid security token. Refresh the page and try again.")

@app.context_processor
def inject_csrf():
    return {"csrf_token": session.get("_csrf_token", "")}

class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    mobile = db.Column(db.String(10), unique=True, nullable=False, index=True)
    land_area = db.Column(db.Float, nullable=False, default=0)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Scheme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(40), nullable=False)
    mode = db.Column(db.String(30), nullable=False)
    benefit = db.Column(db.Text, nullable=False)
    about = db.Column(db.Text, nullable=True)
    min_land = db.Column(db.Float, default=0)
    max_land = db.Column(db.Float, default=9999)
    note = db.Column(db.Text, nullable=True)
    documents_json = db.Column(db.Text, default="[]")
    apply_link = db.Column(db.String(500), nullable=True)
    form_link = db.Column(db.String(500), nullable=True)
    form_label = db.Column(db.String(120), nullable=True)

    @property
    def documents(self):
        try: return json.loads(self.documents_json or "[]")
        except (ValueError, TypeError): return []

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(24), unique=True, nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey("farmer.id"), nullable=False)
    scheme_id = db.Column(db.Integer, db.ForeignKey("scheme.id"), nullable=False)
    problem_type = db.Column(db.String(100), nullable=False)
    applied_on = db.Column(db.Date, nullable=False)
    application_number = db.Column(db.String(100))
    details = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="Submitted")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheme = db.relationship("Scheme")

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("farmer_id"):
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

def current_farmer():
    fid = session.get("farmer_id")
    return db.session.get(Farmer, fid) if fid else None

def eligible(scheme, farmer):
    return farmer.land_area >= scheme.min_land and farmer.land_area <= scheme.max_land

def seed_schemes():
    if Scheme.query.count(): return
    items = json.loads((BASE_DIR / "schemes.json").read_text(encoding="utf-8"))
    for s in items:
        db.session.add(Scheme(id=s["id"], name=s["name"], category=s["category"], level=s["level"],
            mode=s["mode"], benefit=s["benefit"], about=s.get("about"), min_land=s["minLand"],
            max_land=s["maxLand"], note=s.get("note"), documents_json=json.dumps(s.get("docs", []), ensure_ascii=False),
            apply_link=s.get("link"), form_link=s.get("formLink"), form_label=s.get("formLabel")))
    db.session.commit()

@app.context_processor
def inject_globals():
    return {"farmer": current_farmer(), "year": datetime.now().year}

@app.route("/")
def index():
    return redirect(url_for("dashboard") if session.get("farmer_id") else url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        land_text = request.form.get("land_area", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        try: land = float(land_text)
        except ValueError: land = -1
        if len(name) < 2: flash("Please enter your full name.", "error")
        elif not re.fullmatch(r"[6-9]\d{9}", mobile): flash("Enter a valid 10-digit Indian mobile number.", "error")
        elif land < 0 or land > 100000: flash("Enter a valid land area in acres.", "error")
        elif len(password) < 8: flash("Password must contain at least 8 characters.", "error")
        elif password != confirm: flash("Passwords do not match.", "error")
        elif Farmer.query.filter_by(mobile=mobile).first(): flash("This mobile number is already registered. Please log in.", "error")
        else:
            user = Farmer(name=name, mobile=mobile, land_area=land, password_hash=generate_password_hash(password))
            db.session.add(user); db.session.commit()
            session.clear(); session["farmer_id"] = user.id
            flash("Account created successfully. Welcome!", "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        user = Farmer.query.filter_by(mobile=mobile).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear(); session["farmer_id"] = user.id
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        flash("Incorrect mobile number or password.", "error")
    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    session.clear(); flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        mobile = request.form.get("mobile", "").strip()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        # Prototype recovery only. Production must use verified OTP, not identity questions.
        user = Farmer.query.filter_by(mobile=mobile).first()
        if not user or user.name.casefold() != name.casefold():
            flash("We could not verify those details. Please check them or contact support.", "error")
        elif len(password) < 8: flash("New password must contain at least 8 characters.", "error")
        elif password != confirm: flash("Passwords do not match.", "error")
        else:
            user.password_hash = generate_password_hash(password); db.session.commit()
            flash("Password updated. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("forgot.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_farmer()
    all_schemes = Scheme.query.order_by(Scheme.category, Scheme.name).all()
    mine = [s for s in all_schemes if eligible(s, user)]
    mode = request.args.get("view", "eligible")
    visible = mine if mode == "eligible" else all_schemes
    categories = {}
    for s in visible: categories.setdefault(s.category, []).append(s)
    return render_template("dashboard.html", categories=categories, eligible_count=len(mine),
                           total_count=len(all_schemes), view=mode)

@app.route("/scheme/<int:scheme_id>")
@login_required
def scheme_detail(scheme_id):
    scheme = db.session.get(Scheme, scheme_id)
    if not scheme: abort(404)
    return render_template("scheme.html", scheme=scheme, is_eligible=eligible(scheme, current_farmer()))

@app.route("/complaints", methods=["GET", "POST"])
@login_required
def complaints():
    user = current_farmer()
    if request.method == "POST":
        try:
            scheme_id = int(request.form.get("scheme_id", ""))
            applied_on = datetime.strptime(request.form.get("applied_on", ""), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("Please select a scheme and a valid application date.", "error")
            return redirect(url_for("complaints"))
        scheme = db.session.get(Scheme, scheme_id)
        problem = request.form.get("problem_type", "").strip()
        details = request.form.get("details", "").strip()
        if not scheme or not problem or len(details) < 10:
            flash("Please complete all required fields. Describe the problem in at least 10 characters.", "error")
        else:
            ref = "TFS-" + secrets.token_hex(4).upper()
            item = Complaint(reference=ref, farmer_id=user.id, scheme_id=scheme.id, problem_type=problem,
                applied_on=applied_on, application_number=request.form.get("application_number","").strip(),
                details=details)
            db.session.add(item); db.session.commit()
            flash(f"Complaint submitted. Your reference number is {ref}. Save it for future reference.", "success")
            return redirect(url_for("complaints"))
    all_schemes = Scheme.query.order_by(Scheme.name).all()
    mine = Complaint.query.filter_by(farmer_id=user.id).order_by(Complaint.created_at.desc()).all()
    return render_template("complaints.html", schemes=all_schemes, complaints=mine)

@app.errorhandler(404)
def not_found(_): return render_template("404.html"), 404

with app.app_context():
    db.create_all()
    seed_schemes()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
