"""
PDF Generation Service — certificates with QR verification + instructor signature.
"""

import io
import logging

from django.conf import settings
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)


class PDFService:
    """Generate PDF certificates with background, QR code, and instructor signature."""

    BASE_WIDTH, BASE_HEIGHT = landscape(A4)
    PDF_PATH = settings.CERTIFICATES_PDF_PATH

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def generate_certificate_pdf(certificate, template=None):
        """
        Generate a PDF certificate file.

        Returns:
            dict: {'success': bool, 'path': str|None, 'filename': str|None, 'message': str}
        """
        try:
            PDFService.PDF_PATH.mkdir(parents=True, exist_ok=True)

            filename = (
                f"{certificate.participant.id}_"
                f"{certificate.event.id}_"
                f"{certificate.verification_code}.pdf"
            )
            filepath = PDFService.PDF_PATH / filename

            c = canvas.Canvas(str(filepath), pagesize=landscape(A4))

            # Background
            PDFService._draw_background(c, template)

            # Layout config from template (may be empty dict)
            layout = template.layout_config if template else {}

            # Text fields
            student_name = (
                f"{certificate.participant.first_name} "
                f"{certificate.participant.last_name}"
            ).upper()
            event_name = certificate.event.name.upper()
            event_date = certificate.event.event_date.strftime("%d de %B de %Y")
            expires_at = (
                certificate.expires_at.strftime("%d/%m/%Y")
                if certificate.expires_at
                else "N/A"
            )

            PDFService._draw_text(
                c,
                student_name,
                layout.get("student_name", {}),
                PDFService.BASE_WIDTH / 2,
                PDFService.BASE_HEIGHT - 3.2 * inch,
                28,
                color_primary=HexColor("#1e3a8a"),
            )
            PDFService._draw_text(
                c,
                event_name,
                layout.get("event_name", {}),
                1.5 * inch,
                PDFService.BASE_HEIGHT - 4.0 * inch,
                18,
                color_primary=HexColor("#1e3a8a"),
            )
            PDFService._draw_text(
                c,
                f"Realizado el: {event_date}",
                layout.get("event_date", {}),
                1.5 * inch,
                PDFService.BASE_HEIGHT - 4.5 * inch,
                14,
                color_primary=HexColor("#94a3b8"),
            )

            # Bottom-left: verification code + validity (repositioned to avoid QR overlap)
            PDFService._draw_text(
                c,
                f"Código: {certificate.verification_code}",
                layout.get("verification_code", {}),
                0.5 * inch,
                0.85 * inch,
                9,
                color_primary=HexColor("#64748b"),
            )
            PDFService._draw_text(
                c,
                f"Válido hasta: {expires_at}",
                {},
                0.5 * inch,
                0.6 * inch,
                9,
                color_primary=HexColor("#64748b"),
            )

            # QR code — bottom-right corner
            PDFService._draw_qr_code(
                c,
                certificate.verification_code,
                layout.get("qr_code", {}),
            )

            # Instructor signature — bottom-center
            # Prefer event instructor; fall back to ad-hoc signature in layout_config
            instructor = getattr(certificate.event, "instructor", None)
            sig_config = layout.get("signature", {})
            if instructor:
                PDFService._draw_instructor_signature(c, instructor, sig_config)
            elif sig_config:
                PDFService._draw_custom_signature(c, sig_config)

            c.save()
            logger.info("PDF generated: %s", filepath)

            return {
                "success": True,
                "path": f"/certificates/pdfs/{filename}",
                "filename": filename,
                "message": "PDF generated successfully",
            }

        except Exception as exc:
            logger.error("Error generating PDF: %s", exc)
            return {
                "success": False,
                "path": None,
                "filename": None,
                "message": f"PDF generation error: {exc}",
            }

    @staticmethod
    def generate_bulk_pdfs(certificates):
        """Generate PDFs for multiple certificates.

        Returns:
            dict: {'generated': int, 'failed': int, 'errors': list}
        """
        results = {"generated": 0, "failed": 0, "errors": []}

        for cert in certificates:
            template = cert.template if cert.template_id else None
            result = PDFService.generate_certificate_pdf(cert, template)

            if result["success"]:
                cert.pdf_url = result["path"]
                cert.save()
                results["generated"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(
                    {
                        "certificate_id": str(cert.id),
                        "error": result["message"],
                    }
                )

        return results

    # ------------------------------------------------------------------ #
    #  QR code                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _generate_qr_image(verification_code):
        """Return a BytesIO PNG of the QR code pointing to the verify URL."""
        import qrcode

        base_url = getattr(
            settings, "CERTIFICATE_VERIFY_BASE_URL", "http://localhost:8000"
        )
        verify_url = f"{base_url}/api/certificates/verify/?code={verification_code}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf, verify_url

    @staticmethod
    def _draw_qr_code(c, verification_code, config=None):
        """Embed QR code in the bottom-right corner of the certificate."""
        config = config or {}
        try:
            buf, _ = PDFService._generate_qr_image(verification_code)

            qr_size = config.get("size", 1.35) * inch
            x = config.get("x", (PDFService.BASE_WIDTH - qr_size - 0.4 * inch))
            y = config.get("y", 0.35 * inch)

            c.drawImage(
                ImageReader(buf), x, y, width=qr_size, height=qr_size, mask="auto"
            )

            # Label below QR
            c.setFont("Helvetica", 6)
            c.setFillColor(HexColor("#94a3b8"))
            c.drawCentredString(
                x + qr_size / 2, y - 0.13 * inch, "Escanea para verificar"
            )

        except Exception as exc:
            logger.warning("Could not draw QR code: %s", exc)

    # ------------------------------------------------------------------ #
    #  Instructor signature                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _draw_instructor_signature(c, instructor, config=None):
        """
        Draw instructor signature image + line + name at bottom-center.

        Gracefully skips if instructor is None or signature image is unavailable.
        """
        config = config or {}
        if not instructor:
            return

        sig_cx = PDFService.BASE_WIDTH / 2
        line_y = config.get("line_y", 1.05) * inch
        name_y = config.get("name_y", 0.70) * inch
        spec_y = name_y - 0.22 * inch
        sig_w = config.get("sig_width", 2.2) * inch
        sig_h = config.get("sig_height", 0.75) * inch
        sig_y = line_y + 0.08 * inch

        # Signature image (prefer uploaded file, fall back to signature_url path)
        sig_drawn = False
        sig_path = None

        if getattr(instructor, "signature_image", None):
            try:
                sig_path = instructor.signature_image.path
            except Exception:
                sig_path = None

        if sig_path:
            try:
                c.drawImage(
                    ImageReader(sig_path),
                    sig_cx - sig_w / 2,
                    sig_y,
                    width=sig_w,
                    height=sig_h,
                    mask="auto",
                    preserveAspectRatio=True,
                )
                sig_drawn = True
            except Exception as exc:
                logger.warning("Could not load instructor signature image: %s", exc)

        # Horizontal signature line
        c.setLineWidth(0.8)
        c.setStrokeColor(HexColor("#475569"))
        c.line(sig_cx - 1.2 * inch, line_y, sig_cx + 1.2 * inch, line_y)

        # Instructor name
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(HexColor("#1e3a8a"))
        name_text = PDFService._fit_text(
            instructor.full_name, "Helvetica-Bold", 9, 2.5 * inch
        )
        c.drawCentredString(sig_cx, name_y, name_text)

        # Specialty / role
        if instructor.specialty:
            c.setFont("Helvetica", 8)
            c.setFillColor(HexColor("#64748b"))
            spec_text = PDFService._fit_text(
                instructor.specialty, "Helvetica", 8, 2.5 * inch
            )
            c.drawCentredString(sig_cx, spec_y, spec_text)

    @staticmethod
    def _draw_custom_signature(c, config):
        """Draw an ad-hoc signature from layout_config (no Instructor model needed)."""
        sig_cx = PDFService.BASE_WIDTH / 2
        line_y = config.get("line_y", 1.05) * inch
        name_y = config.get("name_y", 0.70) * inch
        spec_y = name_y - 0.22 * inch
        sig_w = config.get("sig_width", 2.2) * inch
        sig_h = config.get("sig_height", 0.75) * inch
        sig_y = line_y + 0.08 * inch

        image_path = config.get("image_path")
        if image_path:
            try:
                c.drawImage(
                    ImageReader(image_path),
                    sig_cx - sig_w / 2,
                    sig_y,
                    width=sig_w,
                    height=sig_h,
                    mask="auto",
                    preserveAspectRatio=True,
                )
            except Exception as exc:
                logger.warning("Could not draw custom signature: %s", exc)

        # Signature line
        c.setLineWidth(0.8)
        c.setStrokeColor(HexColor("#475569"))
        c.line(sig_cx - 1.2 * inch, line_y, sig_cx + 1.2 * inch, line_y)

        instructor_name = config.get("instructor_name", "")
        if instructor_name:
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(HexColor("#1e3a8a"))
            name_text = PDFService._fit_text(
                instructor_name, "Helvetica-Bold", 9, 2.5 * inch
            )
            c.drawCentredString(sig_cx, name_y, name_text)

        specialty = config.get("instructor_specialty", "")
        if specialty:
            c.setFont("Helvetica", 8)
            c.setFillColor(HexColor("#64748b"))
            spec_text = PDFService._fit_text(specialty, "Helvetica", 8, 2.5 * inch)
            c.drawCentredString(sig_cx, spec_y, spec_text)

    # ------------------------------------------------------------------ #
    #  Background                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _draw_background(c, template):
        """Draw template background image or default styled background."""
        if template and template.background_image:
            try:
                c.drawImage(
                    ImageReader(template.background_image.path),
                    0,
                    0,
                    width=PDFService.BASE_WIDTH,
                    height=PDFService.BASE_HEIGHT,
                )
                return
            except Exception as exc:
                logger.warning("Could not load template background: %s", exc)
        PDFService._draw_default_background(c)

    @staticmethod
    def _draw_default_background(c):
        color_primary = HexColor("#1e3a8a")
        color_secondary = HexColor("#94a3b8")

        c.setFillColor(HexColor("#f8fafc"))
        c.rect(
            0, 0, PDFService.BASE_WIDTH, PDFService.BASE_HEIGHT, fill=True, stroke=False
        )

        c.setLineWidth(3)
        c.setStrokeColor(color_primary)
        c.rect(
            0.3 * inch,
            0.3 * inch,
            PDFService.BASE_WIDTH - 0.6 * inch,
            PDFService.BASE_HEIGHT - 0.6 * inch,
        )

        c.setFont("Helvetica-Bold", 48)
        c.setFillColor(color_primary)
        c.drawCentredString(
            PDFService.BASE_WIDTH / 2,
            PDFService.BASE_HEIGHT - 1.5 * inch,
            "CERTIFICADO",
        )

        c.setFont("Helvetica", 24)
        c.setFillColor(color_secondary)
        c.drawCentredString(
            PDFService.BASE_WIDTH / 2,
            PDFService.BASE_HEIGHT - 2.2 * inch,
            "DE ASISTENCIA Y PARTICIPACIÓN",
        )

    # ------------------------------------------------------------------ #
    #  Text helpers                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _fit_text(text, font_name, font_size, max_width):
        """Truncate text with '...' so it never exceeds max_width points."""
        from reportlab.pdfbase.pdfmetrics import stringWidth

        if stringWidth(text, font_name, font_size) <= max_width:
            return text
        while text and stringWidth(text + "...", font_name, font_size) > max_width:
            text = text[:-1]
        return text + "..."

    @staticmethod
    def _draw_text(
        c, text, config, default_x, default_y, default_size, color_primary=None
    ):
        x = (
            config.get("x", default_x / inch) * inch
            if isinstance(config.get("x"), (int, float))
            else default_x
        )
        y = (
            config.get("y", default_y / inch) * inch
            if isinstance(config.get("y"), (int, float))
            else default_y
        )
        font_size = config.get("font_size", default_size)
        font_family = config.get("font_family", "Helvetica")
        color = config.get("color", "#000000")
        centered = config.get("centered", False)

        font_name = f"{font_family}-Bold" if "Bold" not in font_family else font_family
        margin = 1 * inch

        if centered or (isinstance(x, (int, float)) and x > PDFService.BASE_WIDTH / 2):
            max_width = PDFService.BASE_WIDTH - 2 * margin
        else:
            max_width = PDFService.BASE_WIDTH - x - margin

        text = PDFService._fit_text(text, font_name, font_size, max_width)

        c.setFont(font_name, font_size)
        c.setFillColor(HexColor(color) if color_primary is None else color_primary)

        if centered or (isinstance(x, (int, float)) and x > PDFService.BASE_WIDTH / 2):
            c.drawCentredString(x, y, text)
        else:
            c.drawString(x, y, text)
