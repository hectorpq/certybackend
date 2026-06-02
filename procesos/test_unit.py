import pytest
from django.test import SimpleTestCase

from procesos.services import ExcelProcessingResult


@pytest.mark.unit
class ExcelProcessingResultTest(SimpleTestCase):
    def test_add_error_increments_failed(self):
        r = ExcelProcessingResult()
        r.add_error(1, "email", "Invalid email")
        self.assertEqual(r.failed, 1)
        self.assertEqual(len(r.errors), 1)

    def test_add_success_increments_successful(self):
        r = ExcelProcessingResult()
        r.add_success(42)
        self.assertEqual(r.successful, 1)
        self.assertIn(42, r.created_certificates)

    def test_to_dict_keys(self):
        r = ExcelProcessingResult()
        r.total_rows = 5
        r.add_success(1)
        d = r.to_dict()
        for key in ["total_rows", "successful", "failed", "errors", "summary"]:
            self.assertIn(key, d)

    def test_get_summary_with_rows(self):
        r = ExcelProcessingResult()
        r.total_rows = 2
        r.add_success(1)
        s = r.get_summary()
        self.assertIsInstance(s, str)

    def test_get_summary_with_errors(self):
        r = ExcelProcessingResult()
        r.total_rows = 3
        for i in range(12):
            r.add_error(i + 1, "field", f"Error {i}")
        s = r.get_summary()
        self.assertIn("ERRORES", s)
