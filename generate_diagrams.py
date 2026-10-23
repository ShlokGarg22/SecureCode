#!/usr/bin/env python3
"""
Generate high-resolution architecture diagrams for the SecureCode Project Report.
Uses Pillow to produce clean, professional engineering schematics.
"""

import os
from PIL import Image, ImageDraw, ImageFont

DIAGRAM_DIR = "diagrams"
os.makedirs(DIAGRAM_DIR, exist_ok=True)

# Fonts
FONT_TITLE = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 24)
FONT_HEADING = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 18)
FONT_SUB = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
FONT_BODY = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 13)
FONT_BOLD = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 13)
FONT_CODE = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 12)

# Colors
BG_CANVAS = (248, 250, 252)
COLOR_PRIMARY = (30, 58, 138)       # Navy #1E3A8A
COLOR_PRIMARY_BG = (239, 246, 255)  # Light Blue
COLOR_ACCENT = (14, 116, 144)       # Teal/Cyan
COLOR_ACCENT_BG = (240, 253, 250)
COLOR_TEXT_MAIN = (15, 23, 42)
COLOR_TEXT_MUTED = (71, 85, 105)
COLOR_BORDER = (203, 213, 225)
COLOR_BOX_BG = (255, 255, 255)
COLOR_ARROW = (51, 65, 85)
COLOR_SUCCESS_BORDER = (22, 101, 52)
COLOR_SUCCESS_BG = (240, 253, 244)


def draw_rounded_card(draw, box, fill, outline, width=2, radius=8):
    """Draw a smooth rounded rectangle card."""
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_arrow(draw, start, end, color=COLOR_ARROW, width=2, arrow_size=8):
    """Draw a straight arrow from start (x, y) to end (x, y)."""
    draw.line([start, end], fill=color, width=width)
    x1, y1 = start
    x2, y2 = end
    
    # Horizontal arrow
    if y1 == y2:
        if x2 > x1:
            points = [(x2, y2), (x2 - arrow_size, y2 - arrow_size // 2), (x2 - arrow_size, y2 + arrow_size // 2)]
        else:
            points = [(x2, y2), (x2 + arrow_size, y2 - arrow_size // 2), (x2 + arrow_size, y2 + arrow_size // 2)]
        draw.polygon(points, fill=color)
    # Vertical arrow
    elif x1 == x2:
        if y2 > y1:
            points = [(x2, y2), (x2 - arrow_size // 2, y2 - arrow_size), (x2 + arrow_size // 2, y2 - arrow_size)]
        else:
            points = [(x2, y2), (x2 - arrow_size // 2, y2 + arrow_size), (x2 + arrow_size // 2, y2 + arrow_size)]
        draw.polygon(points, fill=color)


def generate_system_architecture():
    """Generates Figure 1: High-Level System Architecture."""
    w, h = 1400, 720
    img = Image.new("RGB", (w, h), BG_CANVAS)
    draw = ImageDraw.Draw(img)

    # Title Banner
    draw.text((40, 30), "Figure 1: SecureCode End-to-End System Architecture", fill=COLOR_PRIMARY, font=FONT_TITLE)
    draw.text((40, 65), "Autonomous Zero-Hosting CI/CD Pipeline from Code Commit to AI Remediation and SARIF Export", fill=COLOR_TEXT_MUTED, font=FONT_SUB)
    draw.line([(40, 95), (1360, 95)], fill=COLOR_BORDER, width=1)

    # Column 1: Git Repository Trigger
    c1_box = (40, 130, 280, 650)
    draw_rounded_card(draw, c1_box, COLOR_BOX_BG, COLOR_BORDER, width=2)
    draw.rounded_rectangle((40, 130, 280, 180), radius=8, fill=COLOR_PRIMARY)
    draw.text((60, 145), "1. Source Trigger", fill=(255, 255, 255), font=FONT_HEADING)
    
    draw.text((60, 205), "Developer Push / PR", fill=COLOR_TEXT_MAIN, font=FONT_BOLD)
    draw.text((60, 230), "Event: push / pull_request", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((60, 250), "Branches: main, master", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    
    draw.line([(60, 285), (260, 285)], fill=COLOR_BORDER, width=1)
    draw.text((60, 305), "Target Source Files:", fill=COLOR_TEXT_MAIN, font=FONT_BOLD)
    draw.text((60, 330), "• Application code (*.py)", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((60, 355), "• Config files (.env, yaml)", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((60, 380), "• Git commit delta", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    
    draw.line([(60, 415), (260, 415)], fill=COLOR_BORDER, width=1)
    draw.text((60, 435), "Action Invocation:", fill=COLOR_TEXT_MAIN, font=FONT_BOLD)
    draw.text((60, 460), "uses: SecureCode@main", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((60, 485), "fail-on: 'high'", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((60, 510), "enable-ai: 'true'", fill=COLOR_TEXT_MUTED, font=FONT_CODE)

    # Arrow 1 -> 2
    draw_arrow(draw, (280, 390), (330, 390), color=COLOR_PRIMARY, width=3, arrow_size=12)

    # Column 2: GitHub Actions Runner (Composite Action)
    c2_box = (330, 130, 1020, 650)
    draw_rounded_card(draw, c2_box, COLOR_PRIMARY_BG, COLOR_PRIMARY, width=2)
    draw.rounded_rectangle((330, 130, 1020, 180), radius=8, fill=COLOR_PRIMARY)
    draw.text((350, 145), "2. GitHub Actions Ephemeral Runner (Zero-Hosting Environment)", fill=(255, 255, 255), font=FONT_HEADING)

    # Inside Runner: Module A - Static Analysis Engines
    mod_a = (360, 205, 665, 395)
    draw_rounded_card(draw, mod_a, COLOR_BOX_BG, COLOR_BORDER, width=2)
    draw.text((375, 220), "Dual Static Analysis Engines", fill=COLOR_PRIMARY, font=FONT_BOLD)
    draw.text((375, 250), "• Semgrep AST Engine", fill=COLOR_TEXT_MAIN, font=FONT_BOLD)
    draw.text((390, 275), "- Abstract Syntax Tree rules", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((390, 295), "- Command Injection (os.system)", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((390, 315), "- Path Traversal & Pickle RCE", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((375, 345), "• Gitleaks Secret Detector", fill=COLOR_TEXT_MAIN, font=FONT_BOLD)
    draw.text((390, 370), "- Shannon entropy & regex keys", fill=COLOR_TEXT_MUTED, font=FONT_BODY)

    # Inside Runner: Module B - Normalizer & Deduplication
    mod_b = (705, 205, 990, 395)
    draw_rounded_card(draw, mod_b, COLOR_BOX_BG, COLOR_BORDER, width=2)
    draw.text((720, 220), "Normalizer & Deduplication", fill=COLOR_PRIMARY, font=FONT_BOLD)
    draw.text((720, 250), "• Path Prefix Stripping", fill=COLOR_TEXT_MAIN, font=FONT_BOLD)
    draw.text((735, 275), "- Removes runner junk paths", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((735, 295), "- Clean rule titles & IDs", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((720, 325), "• SHA-256 Fingerprinting", fill=COLOR_TEXT_MAIN, font=FONT_BOLD)
    draw.text((735, 350), "- Stable hash across scans", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((735, 370), "- Severity tallying matrix", fill=COLOR_TEXT_MUTED, font=FONT_BODY)

    # Inside Arrow: A -> B
    draw_arrow(draw, (665, 300), (705, 300), color=COLOR_PRIMARY, width=2, arrow_size=8)

    # Inside Runner: Module C - Hybrid AI Remediation
    mod_c = (360, 425, 990, 625)
    draw_rounded_card(draw, mod_c, COLOR_BOX_BG, COLOR_BORDER, width=2)
    draw.text((375, 440), "Hybrid AI Remediation & Patch Engine", fill=COLOR_PRIMARY, font=FONT_BOLD)
    
    # Sub-box C1: Privacy Redaction
    draw_rounded_card(draw, (380, 470, 560, 605), COLOR_ACCENT_BG, COLOR_ACCENT, width=1)
    draw.text((390, 485), "Privacy Redaction", fill=COLOR_ACCENT, font=FONT_BOLD)
    draw.text((390, 510), "Strips API keys &", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((390, 530), "tokens via regex", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((390, 555), "Extracts 25 lines", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((390, 575), "of source context", fill=COLOR_TEXT_MUTED, font=FONT_BODY)

    # Sub-box C2: Live Groq Inference
    draw_rounded_card(draw, (585, 470, 770, 605), COLOR_SUCCESS_BG, COLOR_SUCCESS_BORDER, width=1)
    draw.text((595, 485), "Live Groq LPU AI", fill=COLOR_SUCCESS_BORDER, font=FONT_BOLD)
    draw.text((595, 510), "Model: gpt-oss-120b", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((595, 535), "131,072 Context", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((595, 555), "Structured JSON diff", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((595, 575), "Latency: ~1.2s", fill=COLOR_TEXT_MUTED, font=FONT_BODY)

    # Sub-box C3: Fallback Knowledge Base
    draw_rounded_card(draw, (795, 470, 970, 605), COLOR_PRIMARY_BG, COLOR_PRIMARY, width=1)
    draw.text((805, 485), "Offline Fallback", fill=COLOR_PRIMARY, font=FONT_BOLD)
    draw.text((805, 510), "Deterministic engine", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((805, 530), "Zero-network safe", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((805, 555), "Pre-computed fixes", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((805, 575), "Guarantees CI uptime", fill=COLOR_TEXT_MUTED, font=FONT_BODY)

    draw_arrow(draw, (560, 540), (585, 540), color=COLOR_PRIMARY, width=2, arrow_size=6)
    draw_arrow(draw, (770, 540), (795, 540), color=COLOR_PRIMARY, width=2, arrow_size=6)

    # Arrow 2 -> 3
    draw_arrow(draw, (1020, 390), (1070, 390), color=COLOR_PRIMARY, width=3, arrow_size=12)

    # Column 3: Deliverables & Outputs
    c3_box = (1070, 130, 1360, 650)
    draw_rounded_card(draw, c3_box, COLOR_BOX_BG, COLOR_BORDER, width=2)
    draw.rounded_rectangle((1070, 130, 1360, 180), radius=8, fill=COLOR_PRIMARY)
    draw.text((1090, 145), "3. Outputs & Artifacts", fill=(255, 255, 255), font=FONT_HEADING)

    # Output 1: Step Summary
    draw_rounded_card(draw, (1090, 205, 1340, 325), COLOR_PRIMARY_BG, COLOR_PRIMARY, width=1)
    draw.text((1105, 220), "Actions Step Summary", fill=COLOR_PRIMARY, font=FONT_BOLD)
    draw.text((1105, 245), "• Markdown severity matrix", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((1105, 265), "• Auto-expanded High/Critical", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((1105, 285), "• Attack scenarios & fixes", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((1105, 305), "• Syntax-highlighted diffs", fill=COLOR_TEXT_MUTED, font=FONT_BODY)

    # Output 2: SARIF v2.1.0
    draw_rounded_card(draw, (1090, 350, 1340, 470), COLOR_ACCENT_BG, COLOR_ACCENT, width=1)
    draw.text((1105, 365), "OASIS SARIF Report", fill=COLOR_ACCENT, font=FONT_BOLD)
    draw.text((1105, 390), "• results.sarif (v2.1.0)", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((1105, 410), "• Strict artifactChanges fix", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((1105, 430), "• Native GitHub Code", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((1105, 450), "  Scanning security alerts", fill=COLOR_TEXT_MUTED, font=FONT_BODY)

    # Output 3: Remediation Patch
    draw_rounded_card(draw, (1090, 495, 1340, 625), COLOR_SUCCESS_BG, COLOR_SUCCESS_BORDER, width=1)
    draw.text((1105, 510), "Unified Git Patch", fill=COLOR_SUCCESS_BORDER, font=FONT_BOLD)
    draw.text((1105, 535), "• remediation.patch", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((1105, 555), "• Multi-file unified diff", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((1105, 575), "• 1-Click developer fix:", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((1105, 595), "  $ git apply remediation.patch", fill=COLOR_TEXT_MAIN, font=FONT_CODE)

    img.save(os.path.join(DIAGRAM_DIR, "system_architecture.png"), quality=95)
    print("  [+] Generated: diagrams/system_architecture.png")


def generate_data_flow_pipeline():
    """Generates Figure 2: Finding Remediation Pipeline."""
    w, h = 1400, 520
    img = Image.new("RGB", (w, h), BG_CANVAS)
    draw = ImageDraw.Draw(img)

    draw.text((40, 25), "Figure 2: Vulnerability Analysis & AI Patch Generation Pipeline", fill=COLOR_PRIMARY, font=FONT_TITLE)
    draw.text((40, 60), "Step-by-step transformation from raw source vulnerability to verified git remediation patch", fill=COLOR_TEXT_MUTED, font=FONT_SUB)
    draw.line([(40, 85), (1360, 85)], fill=COLOR_BORDER, width=1)

    steps = [
        ("Step 1: Detection", "Static Analysis", ["• Semgrep flags rule", "• Gitleaks catches secret", "• Line & file recorded"], COLOR_PRIMARY_BG, COLOR_PRIMARY),
        ("Step 2: Context", "Source Slicing", ["• Reads target file", "• Slices +/- 12 lines", "• Regex redacts keys"], COLOR_ACCENT_BG, COLOR_ACCENT),
        ("Step 3: Prompting", "Groq LPU Inference", ["• Prompts gpt-oss-120b", "• Requests strict JSON", "• Low temp (0.1) for code"], COLOR_SUCCESS_BG, COLOR_SUCCESS_BORDER),
        ("Step 4: Parsing", "Validation & Diff", ["• Parses plain explanation", "• Validates attack vector", "• Extracts unified diff"], COLOR_PRIMARY_BG, COLOR_PRIMARY),
        ("Step 5: Compilation", "remediation.patch", ["• Formats git headers", "• Aggregates chunks", "• Verifies git apply syntax"], COLOR_ACCENT_BG, COLOR_ACCENT)
    ]

    card_w = 230
    card_h = 360
    start_x = 40
    y = 115

    for idx, (step_num, title, items, fill_col, border_col) in enumerate(steps):
        x = start_x + idx * (card_w + 35)
        draw_rounded_card(draw, (x, y, x + card_w, y + card_h), fill_col, border_col, width=2)
        draw.rounded_rectangle((x, y, x + card_w, y + 45), radius=8, fill=border_col)
        draw.text((x + 15, y + 12), step_num, fill=(255, 255, 255), font=FONT_BOLD)
        
        draw.text((x + 15, y + 65), title, fill=COLOR_TEXT_MAIN, font=FONT_BOLD)
        draw.line([(x + 15, y + 90), (x + card_w - 15, y + 90)], fill=COLOR_BORDER, width=1)
        
        curr_y = y + 110
        for item in items:
            draw.text((x + 15, curr_y), item, fill=COLOR_TEXT_MUTED, font=FONT_BODY)
            curr_y += 35

        # Draw connecting arrow between cards
        if idx < len(steps) - 1:
            arr_start = (x + card_w, y + card_h // 2)
            arr_end = (x + card_w + 35, y + card_h // 2)
            draw_arrow(draw, arr_start, arr_end, color=COLOR_PRIMARY, width=2, arrow_size=8)

    img.save(os.path.join(DIAGRAM_DIR, "data_flow_pipeline.png"), quality=95)
    print("  [+] Generated: diagrams/data_flow_pipeline.png")


def generate_sarif_integration():
    """Generates Figure 3: GitHub SARIF Security Tab Integration."""
    w, h = 1400, 420
    img = Image.new("RGB", (w, h), BG_CANVAS)
    draw = ImageDraw.Draw(img)

    draw.text((40, 25), "Figure 3: OASIS SARIF v2.1.0 GitHub Security Tab Integration", fill=COLOR_PRIMARY, font=FONT_TITLE)
    draw.text((40, 60), "Mapping Internal ScanResult Models directly to Native GitHub Code Scanning Alerts", fill=COLOR_TEXT_MUTED, font=FONT_SUB)
    draw.line([(40, 85), (1360, 85)], fill=COLOR_BORDER, width=1)

    # Box 1: ScanResult
    draw_rounded_card(draw, (40, 115, 380, 370), COLOR_BOX_BG, COLOR_BORDER, width=2)
    draw.rounded_rectangle((40, 115, 380, 160), radius=8, fill=COLOR_PRIMARY)
    draw.text((60, 127), "SecureCode ScanResult Model", fill=(255, 255, 255), font=FONT_BOLD)
    draw.text((60, 185), "• finding_id: DG-8B7C91", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((60, 215), "• rule_id: python-command-injection", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((60, 245), "• file_path: app.py (line 117)", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((60, 275), "• severity: SeverityLevel.CRITICAL", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((60, 305), "• corrected_code: subprocess.run(...)", fill=COLOR_TEXT_MUTED, font=FONT_CODE)

    draw_arrow(draw, (380, 240), (460, 240), color=COLOR_PRIMARY, width=3, arrow_size=10)

    # Box 2: SARIF Exporter Transformation
    draw_rounded_card(draw, (460, 115, 880, 370), COLOR_ACCENT_BG, COLOR_ACCENT, width=2)
    draw.rounded_rectangle((460, 115, 880, 160), radius=8, fill=COLOR_ACCENT)
    draw.text((480, 127), "sarif_exporter.py Transformation", fill=(255, 255, 255), font=FONT_BOLD)
    draw.text((480, 185), "• $schema: sarif-schema-2.1.0.json", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((480, 215), "• runs[0].results[0].ruleId", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((480, 245), "• runs[0].results[0].locations[0].region", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((480, 275), "• runs[0].results[0].fixes[0].artifactChanges", fill=COLOR_TEXT_MAIN, font=FONT_BOLD)
    draw.text((480, 305), "  └─ replacements[0].insertedContent", fill=COLOR_TEXT_MUTED, font=FONT_CODE)
    draw.text((480, 335), "  └─ [Strict OASIS Compliance]", fill=COLOR_SUCCESS_BORDER, font=FONT_BOLD)

    draw_arrow(draw, (880, 240), (960, 240), color=COLOR_PRIMARY, width=3, arrow_size=10)

    # Box 3: GitHub Security Tab
    draw_rounded_card(draw, (960, 115, 1360, 370), COLOR_BOX_BG, COLOR_BORDER, width=2)
    draw.rounded_rectangle((960, 115, 1360, 160), radius=8, fill=COLOR_SUCCESS_BORDER)
    draw.text((980, 127), "GitHub Repository Security Tab", fill=(255, 255, 255), font=FONT_BOLD)
    draw.text((980, 185), "• Tab: Security -> Code scanning alerts", fill=COLOR_TEXT_MAIN, font=FONT_BOLD)
    draw.text((980, 215), "• Native GitHub UI Banner & Alert", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((980, 245), "• Direct inline code annotation", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((980, 275), "• Automatic alert closing upon merge", fill=COLOR_TEXT_MUTED, font=FONT_BODY)
    draw.text((980, 305), "• Enterprise compliance audit trail", fill=COLOR_TEXT_MUTED, font=FONT_BODY)

    img.save(os.path.join(DIAGRAM_DIR, "github_sarif_integration.png"), quality=95)
    print("  [+] Generated: diagrams/github_sarif_integration.png")


if __name__ == "__main__":
    generate_system_architecture()
    generate_data_flow_pipeline()
    generate_sarif_integration()
