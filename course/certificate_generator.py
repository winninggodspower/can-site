import io
import logging
from pathlib import Path
from django.conf import settings
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATE_PATH = Path(settings.BASE_DIR) / 'static' / 'certificates' / 'leadership_certificate_template.pdf'

def generate_leadership_certificate_pdf(certificate, template_path=None) -> bytes:
    """
    Overlays recipient full name, completion date, and verification code
    onto the official Church Arise Network Leadership Certificate template.
    """
    if template_path is None:
        template_path = DEFAULT_TEMPLATE_PATH

    template_path = Path(template_path)
    if not template_path.exists():
        raise FileNotFoundError(f"Certificate template not found at {template_path}")

    # Read base template
    reader = PdfReader(str(template_path))
    base_page = reader.pages[0]

    mb_upper_x = float(base_page.mediabox.upper_right[0])
    mb_upper_y = float(base_page.mediabox.upper_right[1])

    # Recipient Name determination
    user = certificate.user
    full_name = user.get_full_name().strip()
    recipient_name = full_name if full_name else (user.first_name or user.username)

    # Date formatting
    if certificate.issued_at:
        completion_date = certificate.issued_at.strftime("%B %d, %Y")
    else:
        from django.utils import timezone
        completion_date = timezone.now().strftime("%B %d, %Y")

    cert_code = certificate.certificate_code or ""

    # Create overlay canvas
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(mb_upper_x, mb_upper_y))

    # 1. Recipient Name: Centered horizontally at x=165.0, baseline at y=234.0
    can.setFillColor(colors.HexColor("#161938"))
    
    # Calculate responsive font size to ensure name stays within bounds
    target_name_size = 18.0
    measured_width = can.stringWidth(recipient_name, "Times-BoldItalic", target_name_size)
    max_name_width = 240.0
    if measured_width > max_name_width:
        target_name_size = target_name_size * (max_name_width / measured_width)

    can.setFont("Times-BoldItalic", target_name_size)
    can.drawCentredString(165.0, 234.0, recipient_name)

    # 2. Completion Date: Centered over underline at x=191.0, baseline at y=157.5
    can.setFillColor(colors.HexColor("#2d3748"))
    target_date_size = 8.0
    measured_date_width = can.stringWidth(completion_date, "Helvetica", target_date_size)
    max_date_width = 50.0
    if measured_date_width > max_date_width:
        target_date_size = target_date_size * (max_date_width / measured_date_width)

    can.setFont("Helvetica", target_date_size)
    can.drawCentredString(191.0, 157.5, completion_date)

    # 3. Subtle Verification Footer: Centered at bottom margin (y=20.0)
    if cert_code:
        can.setFillColor(colors.HexColor("#718096"))
        can.setFont("Helvetica", 5.5)
        can.drawCentredString(165.0, 20.0, f"Verify credential: churcharisenetwork.com.ng | Code: {cert_code}")

    can.save()
    packet.seek(0)

    # Merge overlay with template page
    overlay_reader = PdfReader(packet)
    overlay_page = overlay_reader.pages[0]

    fresh_reader = PdfReader(str(template_path))
    merged_page = fresh_reader.pages[0]
    merged_page.merge_page(overlay_page)

    writer = PdfWriter()
    writer.add_page(merged_page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()

def render_certificate_preview_image(certificate, template_path=None, scale=2.5) -> bytes:
    """
    Renders the leadership certificate PDF as a high-resolution PNG image
    for fast browser display and mobile fallback.
    """
    import pypdfium2 as pdfium
    pdf_bytes = generate_leadership_certificate_pdf(certificate, template_path=template_path)
    pdf = pdfium.PdfDocument(pdf_bytes)
    img = pdf[0].render(scale=scale).to_pil()
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    pdf.close()
    return buf.getvalue()
