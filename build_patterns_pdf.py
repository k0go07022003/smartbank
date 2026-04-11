"""Build DESIGN_PATTERNS.pdf from DESIGN_PATTERNS.md.

Uses ReportLab Platypus to render a clean, printable document with
section headings, code blocks, and paragraphs. Intentionally avoids
any full markdown-to-PDF library to keep control over styling.
"""
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Preformatted, PageBreak, HRFlowable)

SRC = "DESIGN_PATTERNS.md"
OUT = "DESIGN_PATTERNS.pdf"

ACCENT = HexColor("#6366f1")
ACCENT_DARK = HexColor("#312e81")
CODE_BG = HexColor("#0f1336")

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleBig", parent=styles["Title"],
    fontName="Helvetica-Bold", fontSize=26, leading=32,
    textColor=ACCENT_DARK, spaceAfter=6,
)
subtitle_style = ParagraphStyle(
    "Sub", parent=styles["Normal"],
    fontSize=11, textColor=HexColor("#6b7280"), spaceAfter=24,
)
h1_style = ParagraphStyle(
    "H1", parent=styles["Heading1"],
    fontName="Helvetica-Bold", fontSize=16, leading=22,
    textColor=ACCENT, spaceBefore=18, spaceAfter=10,
)
body_style = ParagraphStyle(
    "Body", parent=styles["BodyText"],
    fontName="Helvetica", fontSize=10.5, leading=15,
    alignment=TA_JUSTIFY, spaceAfter=8, textColor=black,
)
code_style = ParagraphStyle(
    "Code", parent=styles["Code"],
    fontName="Courier", fontSize=8.5, leading=11,
    leftIndent=10, rightIndent=10,
    backColor=HexColor("#f3f4f6"),
    textColor=HexColor("#1e1b4b"),
    borderPadding=8, spaceBefore=6, spaceAfter=10,
    borderColor=HexColor("#e5e7eb"), borderWidth=0.5,
)


def md_inline(text):
    """Minimal markdown → ReportLab <b>/<i>/<font> inline conversion."""
    # escape XML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # `code` → colored mono
    text = re.sub(
        r"`([^`]+)`",
        r'<font name="Courier" color="#4338ca">\1</font>',
        text,
    )
    # **bold**
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    # *italic*
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    return text


def parse(md_path):
    """Convert a markdown file into a list of Platypus flowables."""
    with open(md_path) as f:
        lines = f.read().splitlines()

    flow = []
    i = 0
    first_h1_seen = False

    while i < len(lines):
        line = lines[i]

        # top-level title
        if line.startswith("# ") and not first_h1_seen:
            flow.append(Paragraph(md_inline(line[2:]), title_style))
            flow.append(Paragraph(
                "SmartBank — Software Engineering project documentation",
                subtitle_style))
            flow.append(HRFlowable(width="100%", thickness=1.2,
                                    color=ACCENT, spaceAfter=14))
            first_h1_seen = True
            i += 1
            continue

        # ## section
        if line.startswith("## "):
            flow.append(Paragraph(md_inline(line[3:]), h1_style))
            i += 1
            continue

        # horizontal rule
        if line.strip() == "---":
            flow.append(Spacer(1, 6))
            flow.append(HRFlowable(width="100%", thickness=0.5,
                                    color=HexColor("#d1d5db")))
            flow.append(Spacer(1, 6))
            i += 1
            continue

        # fenced code block
        if line.startswith("```"):
            j = i + 1
            code_lines = []
            while j < len(lines) and not lines[j].startswith("```"):
                code_lines.append(lines[j])
                j += 1
            code = "\n".join(code_lines)
            flow.append(Preformatted(code, code_style))
            i = j + 1
            continue

        # blank line separator
        if line.strip() == "":
            i += 1
            continue

        # gather a paragraph of consecutive non-empty non-block lines
        para = [line]
        j = i + 1
        while (j < len(lines) and lines[j].strip() != ""
               and not lines[j].startswith(("#", "```", "---"))):
            para.append(lines[j])
            j += 1
        text = " ".join(para)
        flow.append(Paragraph(md_inline(text), body_style))
        i = j

    return flow


def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="SmartBank — Design Patterns",
        author="SmartBank Team (Bober, Bialik, Adamek)",
    )
    doc.build(parse(SRC))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
