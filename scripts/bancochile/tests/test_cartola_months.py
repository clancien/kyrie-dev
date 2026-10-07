import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from bancochile_server_core import ServerApiError, extract_movements, has_next_page, month_date_range, month_ranges
from bancochile_server_core import accumulated_cartola, resolve_months


class CartolaMonthTests(unittest.TestCase):
    def test_default_is_three_months_ending_at_hasta(self):
        self.assertEqual([p['month'] for p in resolve_months('', '2026-01')], ['2025-11', '2025-12', '2026-01'])

    def test_all_pages_and_historical_reuse(self):
        account = {'numero': 'test', 'codigoProducto': 'CTD'}
        responses = [
            {'movimientos': [{'id': 1, 'fecha': '20250101'}], 'pagina': [{'masPaginas': 'S'}]},
            {'movimientos': [{'id': 2, 'fecha': '20250102'}], 'pagina': [{'masPaginas': 'N'}]},
        ]
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'cartola.sqlite3'
            with patch('bancochile_server_core.call_post', side_effect=responses) as post:
                result = accumulated_cartola(None, [account], month_ranges('2025-01', '2025-01'), database, 100)
                self.assertEqual(len(result[0]), 2)
                self.assertEqual([c.args[2]['cabecera']['paginacionDesde'] for c in post.call_args_list], [1, 101])
            with patch('bancochile_server_core.call_post') as post:
                result = accumulated_cartola(None, [account], month_ranges('2025-01', '2025-01'), database, 100)
                post.assert_not_called()
                self.assertEqual(len(result[0]), 2)
            with patch('bancochile_server_core.call_post', return_value={'movimientos': [], 'pagina': [{'masPaginas': 'N'}]}):
                result = accumulated_cartola(None, [account], month_ranges('2025-02', '2025-02'), database, 100)
                self.assertEqual(len(result[0]), 2)

    def test_failed_month_is_not_marked_complete(self):
        account = {'numero': 'test'}
        response = {'movimientos': [{'id': 1}], 'pagina': [{'masPaginas': 'S'}]}
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'cartola.sqlite3'
            with patch('bancochile_server_core.call_post', return_value=response):
                with self.assertRaises(ServerApiError):
                    accumulated_cartola(None, [account], month_ranges('2025-01', '2025-01'), database, 100)
            with patch('bancochile_server_core.call_post', return_value={'movimientos': [], 'pagina': [{'masPaginas': 'N'}]}) as post:
                accumulated_cartola(None, [account], month_ranges('2025-01', '2025-01'), database, 100)
                post.assert_called_once()

    def test_refresh_includes_stored_start_month(self):
        period = month_ranges('2025-01', '2025-01')
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'cartola.sqlite3'
            with patch('bancochile_server_core.call_post', return_value={'movimientos': [{'id': 1}], 'pagina': [{'masPaginas': 'N'}]}):
                accumulated_cartola(None, [{'numero': 'test'}], period, database, 100)
            with patch('bancochile_server_core.call_post', return_value={'movimientos': [{'id': 1}, {'id': 2}], 'pagina': [{'masPaginas': 'N'}]}) as post:
                result = accumulated_cartola(None, [{'numero': 'test'}], period, database, 100, refresh_from='2025-01')
                post.assert_called_once()
                self.assertEqual(len(result[0]), 2)

    def test_current_month_refreshes_without_duplicating_records(self):
        period = resolve_months()[-1:]
        response = {'movimientos': [{'id': 1}], 'pagina': [{'masPaginas': 'N'}]}
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'cartola.sqlite3'
            with patch('bancochile_server_core.call_post', return_value=response) as post:
                accumulated_cartola(None, [{'numero': 'test'}], period, database, 100)
                result = accumulated_cartola(None, [{'numero': 'test'}], period, database, 100)
                self.assertEqual(post.call_count, 2)
                self.assertEqual(len(result[0]), 1)

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
