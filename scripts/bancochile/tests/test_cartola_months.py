import unittest

from bancochile_server_core import ServerApiError, extract_movements, has_next_page, month_date_range, month_ranges


class CartolaMonthTests(unittest.TestCase):
    def test_builds_month_ranges_across_year_boundary(self):
        self.assertEqual(
            [item["month"] for item in month_ranges("2025-12", "2026-02")],
            ["2025-12", "2026-01", "2026-02"],
        )

    def test_uses_chile_timezone_for_month_boundaries(self):
        self.assertEqual(month_date_range("2026-01")["fechaInicio"], "2026-01-01T03:00:00.000Z")
        self.assertEqual(month_date_range("2026-05")["fechaInicio"], "2026-05-01T04:00:00.000Z")

    def test_rejects_invalid_or_reversed_months(self):
        for value in ("2026-13", "0000-01", "9999-12", "2026/01"):
            with self.assertRaises(ServerApiError):
                month_date_range(value)
        with self.assertRaises(ServerApiError):
            month_ranges("2026-02", "2026-01")

    def test_uses_backend_pagination_and_direct_movement_list(self):
        response = {"movimientos": [{"fecha": "20260101"}], "pagina": [{"masPaginas": "N"}]}
        movements = extract_movements(response)
        self.assertEqual(movements, [{"fecha": "20260101"}])
        self.assertFalse(has_next_page(response, movements))
        self.assertTrue(has_next_page({"pagina": [{"masPaginas": "S"}]}, []))


if __name__ == "__main__":
    unittest.main()
