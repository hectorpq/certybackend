from unittest.mock import MagicMock, patch

import pytest
from django.test import SimpleTestCase

from services.pdf_service import PDFService


@pytest.mark.unit
class PDFTextOverflowTest(SimpleTestCase):
    def test_short_text_returned_unchanged(self):
        result = PDFService._fit_text("ANA GARCIA", "Helvetica-Bold", 28, 600)
        self.assertEqual(result, "ANA GARCIA")

    def test_very_long_name_is_truncated(self):
        result = PDFService._fit_text("A" * 200, "Helvetica-Bold", 28, 600)
        self.assertLess(len(result), 200)
        self.assertTrue(result.endswith("..."))

    def test_truncated_text_fits_within_max_width(self):
        from reportlab.pdfbase.pdfmetrics import stringWidth

        long_name = "PARTICIPANTE CON UN NOMBRE MUY LARGO QUE NO CABE " * 5
        max_w = 500
        result = PDFService._fit_text(long_name, "Helvetica-Bold", 28, max_w)
        self.assertLessEqual(stringWidth(result, "Helvetica-Bold", 28), max_w)

    def test_exactly_fitting_text_not_truncated(self):
        from reportlab.pdfbase.pdfmetrics import stringWidth

        text = "JUAN"
        font, size = "Helvetica-Bold", 14
        max_w = stringWidth(text, font, size)
        result = PDFService._fit_text(text, font, size, max_w)
        self.assertEqual(result, text)


@pytest.mark.unit
class EmailLimitTest(SimpleTestCase):
    def test_blocked_when_at_daily_limit(self):
        from services.email_service import GMAIL_DAILY_LIMIT, check_email_limit

        with patch("services.email_service.get_emails_sent_today", return_value=GMAIL_DAILY_LIMIT):
            result = check_email_limit()
        self.assertTrue(result["blocked"])
        self.assertTrue(result["warning"])

    def test_warning_but_not_blocked_at_threshold(self):
        from services.email_service import GMAIL_WARNING_THRESHOLD, check_email_limit

        with patch("services.email_service.get_emails_sent_today", return_value=GMAIL_WARNING_THRESHOLD):
            result = check_email_limit()
        self.assertTrue(result["warning"])
        self.assertFalse(result["blocked"])
        self.assertIsNotNone(result["message"])


@pytest.mark.unit
class PDFCustomSignatureTest(SimpleTestCase):
    def test_draw_custom_signature_with_image_and_text(self):
        mock_c = MagicMock()
        config = {
            "image_path": "/fake/sig.png",
            "instructor_name": "Dr. Custom",
            "instructor_specialty": "Testing Engineering",
        }
        with patch("services.pdf_service.ImageReader", side_effect=Exception("no file")):
            PDFService._draw_custom_signature(mock_c, config)
        mock_c.line.assert_called_once()
        self.assertTrue(mock_c.drawCentredString.called)

    def test_draw_custom_signature_without_image(self):
        mock_c = MagicMock()
        config = {"instructor_name": "Prof. Ghost"}
        PDFService._draw_custom_signature(mock_c, config)
        mock_c.line.assert_called_once()

    def test_draw_custom_signature_empty_config(self):
        mock_c = MagicMock()
        PDFService._draw_custom_signature(mock_c, {})
        mock_c.line.assert_called_once()
        mock_c.drawCentredString.assert_not_called()

    def test_draw_instructor_signature_path_exception_sets_none(self):
        from unittest.mock import PropertyMock

        mock_c = MagicMock()
        mock_instructor = MagicMock()
        type(mock_instructor.signature_image).path = PropertyMock(side_effect=ValueError("no path"))
        PDFService._draw_instructor_signature(mock_c, mock_instructor, {})
        mock_c.line.assert_called_once()
