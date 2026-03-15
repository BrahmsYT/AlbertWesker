from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import jwt
import os
from datetime import datetime, timedelta

from scanner import scan_domain, _normalize_domain
from scoring import calculate_risk_score, get_risk_label, get_aws_risk_label
from models import ScanResult, AWSSecuritySummary
from pdf_report import generate_pdf, generate_lists_pdf
from db import (
    init_db,
    add_to_whitelist, remove_from_whitelist, get_whitelist,
    is_whitelisted,
    save_scan, get_scan_history, get_scan_stats, delete_scan,
    create_user, verify_user, get_user_by_id, get_user_by_username,
)

app = FastAPI(title="Domain Security Scanner")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load environment variables
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# JWT configuration from environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Security hardening: Check for weak default JWT_SECRET at startup
WEAK_JWT_SECRET = JWT_SECRET == "your-secret-key-change-in-production"

# SSRF Protection: Whitelisted domain patterns (basic)
def _is_valid_domain(domain: str) -> bool:
    """Validate domain format to prevent SSRF and invalid inputs."""
    domain = domain.strip().lower()
    if not domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    if domain == "localhost" or domain == "127.0.0.1" or domain == "::1" or domain == "0.0.0.0":
        return False
    if domain.startswith("192.168.") or domain.startswith("10.") or domain.startswith("172."):
        return False  # Private IP ranges
    # Basic domain format check: contains only alphanumeric, dots, and hyphens
    if not all(c.isalnum() or c in ".-" for c in domain):
        return False
    if ".." in domain or domain.count(".") < 1:
        return False  # Must have at least one dot unless whitelist exemption
    return True

# English translations (hardcoded)
TRANSLATIONS = {
    "scanner": "Scanner",
    "history": "History",
    "about": "About",
    "logout": "Logout",
    "scan_results": "Scan Results",
    "risk_score": "Risk Score",
    "findings": "Findings",
    "domain": "Domain",
    "status": "Status",
}

def get_text(key: str, default: str = "") -> str:
    """Get English text"""
    return TRANSLATIONS.get(key, default)


def create_token(user_id: int, username: str, role: str) -> str:
    """Create JWT token"""
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except:
        return None


def get_current_user(request: Request) -> dict:
    """Get current user from request cookies"""
    token = request.cookies.get("token")
    if not token:
        return None
    
    payload = verify_token(token)
    if not payload:
        return None
    
    user = get_user_by_id(payload["user_id"])
    return user


@app.on_event("startup")
def startup():
    init_db()
    # Security check: warn if using default JWT_SECRET in production
    if WEAK_JWT_SECRET:
        import sys
        print("⚠️  WARNING: Using default JWT_SECRET 'your-secret-key-change-in-production'")
        print("   This is INSECURE in production. Set JWT_SECRET environment variable immediately.")
        print("   Continuing with weak secret for development only.")
        sys.stderr.flush()


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    lang = request.query_params.get("lang", "en")
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/")
    t = TRANSLATIONS
    return templates.TemplateResponse("login.html", {"request": request, "lang": lang, "t": t})


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    lang = request.query_params.get("lang", "en")
    t = TRANSLATIONS
    
    user = verify_user(username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password", "lang": lang, "t": t},
            status_code=401
        )
    
    token = create_token(user["id"], user["username"], user["role"])
    response = RedirectResponse(url="/", status_code=302)
    # Security hardening: HttpOnly, Secure, SameSite flags
    response.set_cookie(
        "token",
        token,
        path="/",
        max_age=86400,
        httponly=True,  # Prevents JavaScript from accessing cookie
        secure=True,    # Only send over HTTPS
        samesite="Strict"  # CSRF protection: strict origin matching
    )
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    lang = request.query_params.get("lang", "en")
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/")
    t = TRANSLATIONS
    return templates.TemplateResponse("register.html", {"request": request, "lang": lang, "t": t})


@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, username: str = Form(...), password: str = Form(...), email: str = Form(...)):
    lang = request.query_params.get("lang", "en")
    t = TRANSLATIONS
    
    # Check if username already exists
    if get_user_by_username(username):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username already exists", "lang": lang, "t": t},
            status_code=400
        )
    
    # Create new user
    user = create_user(username, password, email, role="user")
    if not user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Registration failed", "lang": lang, "t": t},
            status_code=400
        )
    
    # Log them in
    token = create_token(user["id"], user["username"], user["role"])
    response = RedirectResponse(url="/", status_code=302)
    # Security hardening: HttpOnly, Secure, SameSite flags
    response.set_cookie(
        "token",
        token,
        path="/",
        max_age=86400,
        httponly=True,  # Prevents JavaScript from accessing cookie
        secure=True,    # Only send over HTTPS
        samesite="Strict"  # CSRF protection: strict origin matching
    )
    return response


@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    lang = request.query_params.get("lang", "en")
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("token")
    return response


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    lang = request.query_params.get("lang", "en")
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    t = TRANSLATIONS
    return templates.TemplateResponse("index.html", {"request": request, "lang": lang, "t": t, "user": user})


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    lang = request.query_params.get("lang", "en")
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    t = TRANSLATIONS
    return templates.TemplateResponse("about.html", {"request": request, "lang": lang, "t": t, "user": user})


@app.get("/scan", response_class=HTMLResponse)
async def scan_get(request: Request):
    """Redirect GET requests to home with error message"""
    lang = request.query_params.get("lang", "en")
    t = TRANSLATIONS
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "error": "Please use the form to submit a domain", "lang": lang, "t": t},
        status_code=400,
    )


@app.post("/scan", response_class=HTMLResponse)
async def scan(request: Request, domain: str = Form(...)):
    lang = request.query_params.get("lang", "en")
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    
    t = TRANSLATIONS
    
    # Security: SSRF protection - validate domain format
    if not _is_valid_domain(domain):
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Invalid domain format. Please use a valid domain name.", "lang": lang, "t": t, "user": user},
            status_code=400,
        )
    
    try:
        findings, scan_meta = await scan_domain(domain)
    except ValueError as exc:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": str(exc), "lang": lang, "t": t, "user": user},
            status_code=400,
        )
    except Exception:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "An unexpected error occurred while scanning. Please try again.", "lang": lang, "t": t, "user": user},
            status_code=500,
        )

    score, score_breakdown = calculate_risk_score(findings)
    label = get_risk_label(score)

    # AWS summary is already built in scanner.py, just use it
    # Make sure it's present and has the right structure
    if "aws_summary" not in scan_meta:
        # Fallback if scanner didn't build it (shouldn't happen)
        aws_findings = [f for f in findings if f.code.startswith("AWS_")]
        scan_meta["aws_summary"] = {
            "aws_findings_count": score_breakdown["aws_findings_count"],
            "aws_score_contribution": score_breakdown["aws_score_contribution"],
            "aws_services_detected": scan_meta.get("aws", {}).get("aws_services_detected", []),
            "aws_risk_label": get_aws_risk_label(score_breakdown["aws_score_contribution"]),
            "aws_findings": aws_findings,
        }

    # Save scan to history & auto-categorize into lists
    norm_domain = _normalize_domain(domain)
    save_scan(norm_domain, score, label, len(findings), user_id=user["id"])

    result = ScanResult(
        target=domain.strip(),
        risk_score=score,
        risk_label=label,
        findings=findings,
        is_whitelisted=is_whitelisted(norm_domain),
        scan_meta=scan_meta,
    )

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "result": result,
            "lang": lang,
            "t": TRANSLATIONS,
            "user": user
        },
    )


@app.post("/export-pdf", response_class=Response)
async def export_pdf(request: Request, domain: str = Form(...), export_lang: str = Form("en")):
    """Re-run scan and return PDF report."""
    lang = export_lang if export_lang in TRANSLATIONS else "en"
    try:
        findings, scan_meta = await scan_domain(domain)
    except ValueError as exc:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": str(exc)},
            status_code=400,
        )
    except Exception:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "PDF export failed. Please try again."},
            status_code=500,
        )

    score, score_breakdown = calculate_risk_score(findings)
    label = get_risk_label(score)

    # AWS summary is already built in scanner.py, just use it
    if "aws_summary" not in scan_meta:
        # Fallback if scanner didn't build it
        aws_findings = [f for f in findings if f.code.startswith("AWS_")]
        scan_meta["aws_summary"] = {
            "aws_findings_count": score_breakdown["aws_findings_count"],
            "aws_score_contribution": score_breakdown["aws_score_contribution"],
            "aws_services_detected": scan_meta.get("aws", {}).get("aws_services_detected", []),
            "aws_risk_label": get_aws_risk_label(score_breakdown["aws_score_contribution"]),
            "aws_findings": aws_findings,
        }

    result = ScanResult(
        target=domain.strip(),
        risk_score=score,
        risk_label=label,
        findings=findings,
        is_whitelisted=is_whitelisted(_normalize_domain(domain)),
        scan_meta=scan_meta,
    )

    pdf_bytes = generate_pdf(result, lang=lang)
    safe_name = _normalize_domain(domain).replace(".", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="scan_{safe_name}.pdf"'},
    )


# ── Whitelist management & Scan History ──

@app.get("/lists", response_class=HTMLResponse)
async def lists_page(request: Request):
    lang = request.query_params.get("lang", "en")
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    
    t = TRANSLATIONS
    
    # Admin sees all history, users see only their own
    if user["role"] == "admin":
        history = get_scan_history()
        safe = get_scan_history("safe")
        warning = get_scan_history("warning")
        dangerous = get_scan_history("dangerous")
        stats = get_scan_stats()
    else:
        # User only sees their own scans
        history = []
        safe = []
        warning = []
        dangerous = []
        stats = {"total": 0, "safe": 0, "warning": 0, "dangerous": 0, "uncategorized": 0}
    
    return templates.TemplateResponse(
        "lists.html",
        {
            "request": request,
            "lang": lang,
            "t": t,
            "user": user,
            "whitelist": get_whitelist() if user["role"] == "admin" else [],
            "history": history,
            "safe": safe,
            "warning": warning,
            "dangerous": dangerous,
            "stats": stats,
        },
    )


def _lists_ctx(request: Request, message: str = "", lang: str = "en", user: dict = None) -> dict:
    """Shared context for lists page."""
    t = TRANSLATIONS
    
    # Admin sees all history, users see only their own
    if user and user.get("role") == "admin":
        whitelist = get_whitelist()
        history = get_scan_history()
        safe = get_scan_history("safe")
        warning = get_scan_history("warning")
        dangerous = get_scan_history("dangerous")
        stats = get_scan_stats()
    else:
        whitelist = []
        history = []
        safe = []
        warning = []
        dangerous = []
        stats = {"total": 0, "safe": 0, "warning": 0, "dangerous": 0, "uncategorized": 0}
    
    return {
        "request": request,
        "lang": lang,
        "t": t,
        "user": user,
        "whitelist": whitelist,
        "history": history,
        "safe": safe,
        "warning": warning,
        "dangerous": dangerous,
        "stats": stats,
        "message": message,
    }


@app.post("/lists/whitelist/add", response_class=HTMLResponse)
async def whitelist_add(request: Request, domain: str = Form(...), note: str = Form("")):
    lang = request.query_params.get("lang", "en")
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/lists")
    added = add_to_whitelist(domain, note)
    msg = f"'{domain}' added to whitelist." if added else f"'{domain}' is already in the whitelist."
    return templates.TemplateResponse("lists.html", _lists_ctx(request, msg, lang, user))


@app.post("/lists/whitelist/remove", response_class=HTMLResponse)
async def whitelist_remove(request: Request, domain: str = Form(...)):
    lang = request.query_params.get("lang", "en")
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/lists")
    remove_from_whitelist(domain)
    return templates.TemplateResponse("lists.html", _lists_ctx(request, f"'{domain}' removed from whitelist.", lang, user))


@app.post("/lists/history/delete", response_class=HTMLResponse)
async def history_delete(request: Request, scan_id: int = Form(...)):
    lang = request.query_params.get("lang", "en")
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/lists")
    deleted = delete_scan(scan_id)
    msg = "Scan deleted from history." if deleted else "Scan not found."
    return templates.TemplateResponse("lists.html", _lists_ctx(request, msg, lang, user))


# ── Export Lists as PDF ──

CATEGORY_TITLES = {
    "all": "All Scan History",
    "safe": "Safe Domains (Whitelist)",
    "warning": "Warning Domains",
    "dangerous": "Dangerous Domains",
    "whitelist": "Whitelisted Domains",
}


@app.post("/export-lists", response_class=Response)
async def export_lists(category: str = Form("all")):
    allowed = {"all", "safe", "warning", "dangerous", "whitelist"}
    if category not in allowed:
        category = "all"

    title = CATEGORY_TITLES.get(category, "Domain List")

    if category == "whitelist":
        items = get_whitelist()
        rows = [
            {"domain": i["domain"], "detail": i.get("note", ""), "date": i["added_at"][:10]}
            for i in items
        ]
        columns = ["Domain", "Note", "Added"]
    else:
        cat_filter = None if category == "all" else category
        items = get_scan_history(cat_filter)
        rows = [
            {
                "domain": i["domain"],
                "score": i["risk_score"],
                "risk": i["risk_label"],
                "category": i.get("category", ""),
                "findings": i["finding_count"],
                "date": i["scanned_at"][:16].replace("T", " "),
            }
            for i in items
        ]
        columns = ["Domain", "Score", "Risk", "Category", "Findings", "Scanned"]

    pdf_bytes = generate_lists_pdf(title, columns, rows)
    safe_name = category.replace(" ", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="list_{safe_name}.pdf"'},
    )
