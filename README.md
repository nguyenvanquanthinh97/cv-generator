# CV Generate

A local web-based CV/resume editor and PDF generator, built on [RenderCV](https://docs.rendercv.com/) (Typst-based rendering). Edit your CV through a form in the browser, render it to PDF with one click, and preview the result live — no YAML editing required (though you still can).

## Features

- Form-based editor for basic info, social networks, summary, experience, education, skills, and certifications
- Profile photo upload, shown as a circular headshot on the CV
- Certification entries support an optional URL (e.g. a Credly badge or your LinkedIn certifications page), rendered as a clickable link
- Live PDF preview in the browser after rendering
- Switchable design theme (`classic`, `sb2nov`, `moderncv`, `engineeringresumes`, and more)
- All data is stored in a single, human-editable [`cv.yaml`](cv.yaml) — the editor and the file stay in sync

## Prerequisites

- Python 3.12+ on Windows (tested), macOS, or Linux
- Internet access on first run — RenderCV's PDF/font assets are downloaded on install

## Setup

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

(macOS/Linux: `source .venv/bin/activate && pip install -r requirements.txt`)

## Usage

Start the editor:

```bash
.venv/Scripts/python.exe app.py
```

Then open **http://localhost:5055**.

- **Save** — writes your current form data to `cv.yaml` without rendering a PDF.
- **Render PDF** — saves, then runs RenderCV to regenerate the PDF and updates the live preview pane.
- **Download PDF** — downloads whatever PDF was produced by the last successful render.

> The dev server's auto-reloader is disabled (see [Notes](#notes)). If you edit `app.py` or `cv_data.py`, stop the server (`Ctrl+C`) and restart it to pick up the change. Editing `cv.yaml`, `templates/index.html`, `static/app.js`, or `static/style.css` does **not** require a restart.

## Project structure

```
cv.yaml                 CV data — the source of truth, in RenderCV's schema
cv_data.py               Translates between cv.yaml and the editor's form fields
app.py                    Flask app: serves the editor, saves data, triggers renders
templates/index.html     Editor page
static/app.js             Editor frontend logic
static/style.css          Editor styling
static/uploads/           Uploaded profile photo (replaced on each new upload)
rendercv_output/          Generated cv.pdf, cv_1.png, cv_2.png, cv.typ, cv.md, cv.html (gitignored)
.claude/launch.json       Lets Claude Code preview the app via its built-in browser
```

## Editing directly in `cv.yaml`

The editor covers the common fields, but `cv.yaml` follows the full [RenderCV schema](https://docs.rendercv.com/user_guide/) — you can hand-edit it for anything the form doesn't expose (e.g. publications, projects, custom sections), then reload the editor page to pick up your changes.

## Notes

- RenderCV output filenames are pinned to fixed names (`cv.pdf`, `cv_1.png`, …) via `settings.render_command` in `cv.yaml`, rather than being derived from your name. Do not remove that block — a prior version of this project without it hit a Windows file-locking bug when the name-derived output collided with a stuck file handle.
- Flask's `use_reloader` is disabled in `app.py` for the same reason: on this machine, the reloader was observed alternating between two Python interpreters on restart and leaving orphaned processes that locked output files.

## Privacy

`cv.yaml` contains your real contact details, and `static/uploads/` contains your photo — both are meant to be committed here since they're the CV content itself. The `input/` folder (raw source PDF, original photo, scratch notes) is gitignored and stays local only.
