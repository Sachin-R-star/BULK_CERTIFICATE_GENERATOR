import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.config import OUTPUT_DIR

def get_font(size: int, bold: bool = False):
    """Utility to load system truetype font with fallback to PIL default font."""
    font_names = (
        ["arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["arial.ttf", "arialbd.ttf", "DejaVuSans.ttf", "liberation-sans.ttf"]
    )
    for font_name in font_names:
        try:
            return ImageFont.truetype(font_name, size)
        except IOError:
            continue
    return ImageFont.load_default()

def draw_auto_scaled_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, initial_font_size: int, y_pos: int, fill: str, bold: bool = True):
    """Draws text centered, automatically reducing font size if it exceeds max_width."""
    font_size = initial_font_size
    font = get_font(font_size, bold=bold)
    
    # Scale down font size if text is too wide for certificate boundaries
    while font_size > 14:
        try:
            bbox = font.getbbox(text)
            text_w = bbox[2] - bbox[0]
        except AttributeError:
            text_w = font.getsize(text)[0]
        
        if text_w <= max_width:
            break
        font_size -= 2
        font = get_font(font_size, bold=bold)

    draw.text((1400 / 2, y_pos), text, fill=fill, font=font, anchor="mm")

def generate_pdf_certificate(
    job_id: str,
    certificate_id: str,
    recipient_name: str,
    event_name: str,
    issuer_name: str,
    issue_date: str,
    certificate_code: str
) -> str:
    """
    Generates a high-quality PDF certificate for a recipient using Pillow (PIL).
    Returns the absolute file path of the generated PDF.
    """
    # Intentional failure hook for testing failure resilience
    if "__TRIGGER_FAIL__" in recipient_name:
        raise ValueError(f"Simulated generation failure for recipient '{recipient_name}'")

    # Create job specific output directory
    job_dir = Path(OUTPUT_DIR) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{certificate_code}.pdf"
    file_path = job_dir / filename

    # Canvas dimensions (A4 Landscape aspect ratio: 1400 x 990)
    width, height = 1400, 990
    img = Image.new("RGB", (width, height), "#F8FAFC")
    draw = ImageDraw.Draw(img)

    # --- Background & Double Borders ---
    # Outer Navy Border
    draw.rectangle([25, 25, width - 25, height - 25], outline="#1E3A8A", width=10)
    # Inner Gold Border
    draw.rectangle([36, 36, width - 36, height - 36], outline="#D97706", width=3)

    # Decorative Gold Corner Blocks
    c_size = 18
    draw.rectangle([25, 25, 25 + c_size, 25 + c_size], fill="#D97706")
    draw.rectangle([width - 25 - c_size, 25, width - 25, 25 + c_size], fill="#D97706")
    draw.rectangle([25, height - 25 - c_size, 25 + c_size, height - 25], fill="#D97706")
    draw.rectangle([width - 25 - c_size, height - 25 - c_size, width - 25, height - 25], fill="#D97706")

    # --- Header Section ---
    draw_auto_scaled_text(draw, issuer_name.upper(), max_width=1100, initial_font_size=22, y_pos=110, fill="#4B5563", bold=True)

    # Accent Gold Line under header
    draw.line([(width / 2 - 80, 135), (width / 2 + 80, 135)], fill="#D97706", width=3)

    # Main Title
    draw_auto_scaled_text(draw, "CERTIFICATE OF COMPLETION", max_width=1100, initial_font_size=42, y_pos=210, fill="#1E3A8A", bold=True)

    # Presentation Text
    font_sub = get_font(20, bold=False)
    draw.text((width / 2, 280), "This is proudly presented to", fill="#6B7280", font=font_sub, anchor="mm")

    # --- Recipient Name (with Auto-scaling for long names) ---
    draw_auto_scaled_text(draw, recipient_name, max_width=1100, initial_font_size=44, y_pos=380, fill="#0F172A", bold=True)

    # Underline under Recipient Name
    draw.line([(width / 2 - 250, 415), (width / 2 + 250, 415)], fill="#CBD5E1", width=2)

    # --- Event / Achievement details (with Auto-scaling) ---
    font_body = get_font(20, bold=False)
    draw.text((width / 2, 480), "for successful participation and completion of", fill="#4B5563", font=font_body, anchor="mm")

    draw_auto_scaled_text(draw, event_name, max_width=1100, initial_font_size=32, y_pos=545, fill="#1E3A8A", bold=True)

    # --- Footer Section ---
    # Issue Date & Verification Code (Left)
    font_footer = get_font(18, bold=False)
    draw.text((100, 800), f"Issue Date: {issue_date}", fill="#374151", font=font_footer)
    draw.text((100, 835), f"Certificate ID: {certificate_code}", fill="#6B7280", font=font_footer)

    # Verified Gold Seal (Center)
    seal_x, seal_y, seal_r = width / 2, 820, 50
    draw.ellipse([seal_x - seal_r, seal_y - seal_r, seal_x + seal_r, seal_y + seal_r], fill="#D97706")
    draw.ellipse([seal_x - seal_r + 8, seal_y - seal_r + 8, seal_x + seal_r - 8, seal_y + seal_r - 8], fill="#B45309")
    font_seal = get_font(15, bold=True)
    draw.text((seal_x, seal_y), "OFFICIAL\nVERIFIED", fill="#FFFFFF", font=font_seal, anchor="mm", align="center")

    # Signature Block (Right)
    draw.line([(width - 400, 800), (width - 100, 800)], fill="#374151", width=2)
    font_sig_title = get_font(18, bold=True)
    font_sig_sub = get_font(15, bold=False)
    draw.text((width - 250, 825), "Authorized Signature", fill="#374151", font=font_sig_title, anchor="mm")
    draw.text((width - 250, 850), issuer_name, fill="#6B7280", font=font_sig_sub, anchor="mm")

    # Save as high-resolution PDF file
    img.save(str(file_path), "PDF", resolution=150.0)

    return str(file_path)
