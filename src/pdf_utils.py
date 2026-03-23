"""
Pathology-style disease prediction PDF reports (layout aligned with lab report template).
"""
import os
import re
from datetime import datetime
from io import BytesIO

from fpdf import FPDF

# Header title (optional override via REPORT_HEADER_TITLE)
REPORT_HEADER_TITLE = os.environ.get(
    "REPORT_HEADER_TITLE",
    "Disease Recognition and Test Recommendation System",
)
REPORT_TYPE_LABEL = "Disease Prediction Report"

# Colors (RGB)
COLOR_TEXT = (0, 0, 0)
COLOR_LABEL = (70, 100, 140)
COLOR_BORDER = (209, 220, 229)
COLOR_MUTED = (100, 100, 100)
COLOR_DIAGNOSIS = (255, 0, 0)
COLOR_STAMP = (46, 125, 50)
COLOR_HEADER_LINE = (220, 220, 220)


def _safe(text) -> str:
    if text is None:
        return ""
    s = str(text)
    return s.encode("latin-1", "replace").decode("latin-1")


def short_report_id(report_id: str) -> str:
    """8-char display ID similar to sample receipts."""
    h = re.sub(r"[^a-fA-F0-9]", "", report_id or "")
    if len(h) >= 8:
        return h[:8].upper()
    return (report_id or "UNKNOWN")[:8].upper()


def format_report_datetime(date_value) -> str:
    """DD/MM/YYYY, HH:MM:SS for display."""
    if hasattr(date_value, "strftime"):
        return date_value.strftime("%d/%m/%Y, %H:%M:%S")
    s = str(date_value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19], fmt).strftime("%d/%m/%Y, %H:%M:%S")
        except ValueError:
            continue
    return s


def _parse_list_field(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return [t.strip() for t in str(raw).split(",") if t.strip()]


class DiseaseReportPDF(FPDF):
    def __init__(self):
        super().__init__(format="A4", unit="mm")
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(True, margin=20)


def generate_prediction_report(
    report_id: str,
    date_display: str,
    patient_name: str,
    predicted_disease: str,
    recommended_tests,
    symptoms=None,
):
    """
    Build a pathology-style PDF matching the lab report layout.
    Returns BytesIO with PDF bytes (caller should send as attachment).
    """
    symptoms = _parse_list_field(symptoms)
    tests = _parse_list_field(recommended_tests)
    patient_name = patient_name or "-"
    disease = predicted_disease or "-"
    rid = short_report_id(report_id)

    pdf = DiseaseReportPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    # --- Header ---
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 8, _safe(REPORT_HEADER_TITLE), align="C")
    pdf.set_font("Helvetica", "", 10)

    pdf.set_text_color(*COLOR_HEADER_LINE)
    pdf.line(15, pdf.get_y() + 2, 195, pdf.get_y() + 2)
    pdf.ln(6)

    # --- Metadata 2x2 grid ---
    pdf.set_text_color(*COLOR_TEXT)
    box_w = 85
    box_h = 18
    gap = 5
    y0 = pdf.get_y()
    x_left = 15
    x_right = 15 + box_w + gap

    def draw_meta_box(x, y, label, value):
        pdf.set_xy(x, y)
        pdf.set_draw_color(*COLOR_BORDER)
        pdf.set_line_width(0.3)
        pdf.rect(x, y, box_w, box_h)
        pdf.set_xy(x + 3, y + 3)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*COLOR_LABEL)
        pdf.cell(box_w - 6, 4, _safe(label), ln=1)
        pdf.set_x(x + 3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*COLOR_TEXT)
        pdf.cell(box_w - 6, 7, _safe(value), ln=0)

    draw_meta_box(x_left, y0, "Report / Receipt ID", rid)
    draw_meta_box(x_right, y0, "Date & Time", date_display)
    y1 = y0 + box_h + 4
    draw_meta_box(x_left, y1, "Patient", patient_name)
    draw_meta_box(x_right, y1, "Type", REPORT_TYPE_LABEL)
    pdf.set_y(y1 + box_h + 8)

    # --- Symptoms ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.cell(0, 7, "Symptoms", ln=1)
    pdf.ln(1)
    pdf.set_font("Helvetica", "", 10)
    if not symptoms:
        pdf.set_text_color(*COLOR_MUTED)
        pdf.multi_cell(0, 6, _safe("- No symptoms recorded for this report -"))
        pdf.set_text_color(*COLOR_TEXT)
    else:
        for s in symptoms:
            pdf.cell(5, 6, chr(149), ln=0)  # bullet
            pdf.multi_cell(0, 6, _safe(s))
    pdf.ln(4)

    # --- Diagnosis (highlighted box) ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.cell(0, 7, "Diagnosis", ln=1)
    pdf.ln(1)
    dx, dy = 15, pdf.get_y()
    dw = 180
    dh = 14
    pdf.set_draw_color(*COLOR_BORDER)
    pdf.set_line_width(0.4)
    pdf.rect(dx, dy, dw, dh)
    pdf.set_xy(dx, dy + 3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*COLOR_DIAGNOSIS)
    pdf.cell(dw, 8, _safe(disease), align="C", ln=1)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_y(dy + dh + 6)

    # --- Recommended tests ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Recommended Tests", ln=1)
    pdf.ln(1)
    pdf.set_font("Helvetica", "", 10)
    if not tests:
        pdf.set_text_color(*COLOR_MUTED)
        pdf.multi_cell(0, 6, _safe("- None specified -"))
        pdf.set_text_color(*COLOR_TEXT)
    else:
        for t in tests:
            pdf.cell(5, 6, chr(149), ln=0)
            pdf.multi_cell(0, 6, _safe(t))

    # --- Footer: disclaimer + stamp ---
    pdf.ln(8)
    if pdf.get_y() > 245:
        pdf.add_page()
    # Reserve ~35 mm for disclaimer + stamp row
    if pdf.get_y() + 35 > 282:
        pdf.add_page()
    foot_y = pdf.get_y()
    stamp_w = 58
    stamp_h = 28
    pdf.set_y(foot_y)

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(*COLOR_MUTED)
    disc = (
        "This is a computer generated report for reference only. "
        "Please consult a doctor for medical advice."
    )
    pdf.set_xy(15, foot_y)
    pdf.multi_cell(120, 4, _safe(disc))

    sx = 195 - stamp_w
    sy = foot_y
    pdf.set_draw_color(*COLOR_STAMP)
    pdf.set_line_width(0.8)
    pdf.rect(sx, sy, stamp_w, stamp_h)
    pdf.set_xy(sx, sy + 4)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*COLOR_STAMP)
    pdf.cell(stamp_w, 5, "LAB STAMP", align="C", ln=1)
    pdf.set_x(sx)
    pdf.cell(stamp_w, 5, "DRLOGY", align="C", ln=1)
    pdf.set_x(sx)
    pdf.cell(stamp_w, 5, "PATHOLOGY LAB", align="C", ln=1)

    out = pdf.output(dest="S")
    if isinstance(out, str):
        out = out.encode("latin-1")
    buf = BytesIO(out)
    buf.seek(0)
    return buf
