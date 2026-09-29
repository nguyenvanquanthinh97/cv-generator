"""Read/write cv.yaml, translating between the rendercv YAML schema and the
flat JSON shape the editor's web form works with."""

import re
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent
CV_PATH = BASE_DIR / "cv.yaml"
PHOTO_DIR = BASE_DIR / "static" / "uploads"
SCHEMA_COMMENT = (
    "# yaml-language-server: $schema="
    "https://raw.githubusercontent.com/rendercv/rendercv/refs/tags/v2.8/schema.json\n"
)

MD_LINK = re.compile(r"^\[(?P<text>.*)\]\((?P<url>.*)\)$")

AVAILABLE_THEMES = [
    "classic",
    "sb2nov",
    "moderncv",
    "engineeringresumes",
    "engineeringclassic",
    "ember",
    "harvard",
    "ink",
    "opal",
]


def _split_md_link(value: str) -> dict:
    match = MD_LINK.match(value.strip()) if value else None
    if match:
        return {"text": match.group("text"), "url": match.group("url")}
    return {"text": value or "", "url": ""}


def _to_md_link(text: str, url: str) -> str:
    text = (text or "").strip()
    url = (url or "").strip()
    if url:
        return f"[{text}]({url})"
    return text


def save_photo(filename: str, content: bytes) -> str:
    """Save an uploaded photo, replacing any previous upload, and return its
    path relative to the project root (as rendercv expects for `cv.photo`)."""
    ext = Path(filename).suffix.lower() or ".jpg"
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    for old in PHOTO_DIR.glob("profile.*"):
        old.unlink()
    photo_path = PHOTO_DIR / f"profile{ext}"
    photo_path.write_bytes(content)
    return photo_path.relative_to(BASE_DIR).as_posix()


def current_photo_path() -> Path | None:
    if not PHOTO_DIR.exists():
        return None
    return next(PHOTO_DIR.glob("profile.*"), None)


def load_cv() -> dict:
    raw = yaml.safe_load(CV_PATH.read_text(encoding="utf-8"))
    cv = raw.get("cv", {})
    sections = cv.get("sections", {}) or {}

    social_networks = [
        {"network": sn.get("network", ""), "username": sn.get("username", "")}
        for sn in (cv.get("social_networks") or [])
    ]

    summary_lines = sections.get("summary") or []

    experience = [
        {
            "company": e.get("company", ""),
            "position": e.get("position", ""),
            "summary": e.get("summary", "") or "",
            "location": e.get("location", "") or "",
            "start_date": e.get("start_date", "") or "",
            "end_date": e.get("end_date", "") or "",
            "highlights": e.get("highlights") or [],
        }
        for e in (sections.get("experience") or [])
    ]

    education = [
        {
            "institution": e.get("institution", ""),
            "area": e.get("area", ""),
            "degree": e.get("degree", "") or "",
            "start_date": e.get("start_date", "") or "",
            "end_date": e.get("end_date", "") or "",
            "highlights": e.get("highlights") or [],
        }
        for e in (sections.get("education") or [])
    ]

    skills = [
        {"label": s.get("label", ""), "details": s.get("details", "")}
        for s in (sections.get("skills") or [])
    ]

    certifications = []
    for c in sections.get("certifications") or []:
        parsed = _split_md_link(c.get("name", ""))
        certifications.append(
            {
                "name": parsed["text"],
                "url": parsed["url"],
                "date": c.get("date", "") or "",
            }
        )

    return {
        "name": cv.get("name", ""),
        "headline": cv.get("headline", "") or "",
        "location": cv.get("location", "") or "",
        "email": cv.get("email", "") or "",
        "phone": cv.get("phone", "") or "",
        "website": cv.get("website", "") or "",
        "photo": cv.get("photo", "") or "",
        "social_networks": social_networks,
        "summary": "\n\n".join(summary_lines),
        "experience": experience,
        "education": education,
        "skills": skills,
        "certifications": certifications,
        "theme": (raw.get("design") or {}).get("theme", "classic"),
    }


def save_cv(data: dict) -> None:
    social_networks = [
        {"network": sn["network"], "username": sn["username"]}
        for sn in data.get("social_networks", [])
        if sn.get("network") and sn.get("username")
    ]

    summary_text = (data.get("summary") or "").strip()
    summary_paragraphs = [p.strip() for p in summary_text.split("\n\n") if p.strip()]

    experience = []
    for e in data.get("experience", []):
        if not (e.get("company") or e.get("position")):
            continue
        entry = {
            "company": e.get("company", ""),
            "position": e.get("position", ""),
        }
        if e.get("summary"):
            entry["summary"] = e["summary"]
        if e.get("location"):
            entry["location"] = e["location"]
        entry["start_date"] = e.get("start_date") or None
        entry["end_date"] = e.get("end_date") or None
        highlights = [h for h in e.get("highlights", []) if h.strip()]
        if highlights:
            entry["highlights"] = highlights
        experience.append(entry)

    education = []
    for e in data.get("education", []):
        if not e.get("institution"):
            continue
        entry = {
            "institution": e.get("institution", ""),
            "area": e.get("area", ""),
        }
        if e.get("degree"):
            entry["degree"] = e["degree"]
        entry["start_date"] = e.get("start_date") or None
        entry["end_date"] = e.get("end_date") or None
        highlights = [h for h in e.get("highlights", []) if h.strip()]
        if highlights:
            entry["highlights"] = highlights
        education.append(entry)

    skills = [
        {"label": s["label"], "details": s["details"]}
        for s in data.get("skills", [])
        if s.get("label") and s.get("details")
    ]

    certifications = []
    for c in data.get("certifications", []):
        if not c.get("name"):
            continue
        entry = {"name": _to_md_link(c["name"], c.get("url", ""))}
        if c.get("date"):
            entry["date"] = c["date"]
        certifications.append(entry)

    sections = {}
    if summary_paragraphs:
        sections["summary"] = summary_paragraphs
    if experience:
        sections["experience"] = experience
    if education:
        sections["education"] = education
    if skills:
        sections["skills"] = skills
    if certifications:
        sections["certifications"] = certifications

    doc = {
        "cv": {
            "name": data.get("name", ""),
            "headline": data.get("headline") or None,
            "location": data.get("location") or None,
            "email": data.get("email") or None,
            "phone": data.get("phone") or None,
            "website": data.get("website") or None,
            "photo": data.get("photo") or None,
            "social_networks": social_networks or None,
            "sections": sections,
        },
        "design": {"theme": data.get("theme", "classic")},
        "locale": {"language": "english"},
        "settings": {
            "current_date": "today",
            "render_command": {
                "output_folder": "rendercv_output",
                "typst_path": "OUTPUT_FOLDER/cv.typ",
                "pdf_path": "OUTPUT_FOLDER/cv.pdf",
                "markdown_path": "OUTPUT_FOLDER/cv.md",
                "html_path": "OUTPUT_FOLDER/cv.html",
                "png_path": "OUTPUT_FOLDER/cv.png",
            },
        },
    }

    yaml_text = yaml.dump(
        doc,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=100,
    )
    CV_PATH.write_text(SCHEMA_COMMENT + yaml_text, encoding="utf-8")
