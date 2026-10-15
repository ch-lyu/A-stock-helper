import unittest
from unittest.mock import patch

from astock.providers import fundamentals, history, news, request_json


class ProviderTests(unittest.TestCase):
    def test_news_without_verifiable_date_or_url_is_excluded(self):
        records = [{"新闻标题": "缺日期", "新闻链接": "https://example.com/a"},
                   {"新闻标题": "坏链接", "发布时间": "2024-01-02", "新闻链接": "https:///a"},
                   {"新闻标题": "坏日期", "发布时间": "yesterday", "新闻链接": "https://example.com/b"}]
        with patch("astock.providers.akshare_records", return_value={"records": records}):
            result = news("600519")
        self.assertEqual(result["status"], "DATA_UNAVAILABLE")
        self.assertEqual(len(result["excluded_items"]), 3)
        self.assertEqual(result["items"], [])

    def test_empty_financial_tables_are_unavailable_and_same_day_is_not_known(self):
        with patch("astock.providers.tushare_call", return_value=[]):
            self.assertEqual(fundamentals("600519", "2024-04-30")["status"], "DATA_UNAVAILABLE")
        with patch("astock.providers.tushare_call", return_value=[
                {"ann_date": "20240430"}, {"ann_date": "20240429"}, {"end_date": "20240331"}]):
            result = fundamentals("600519", "2024-04-30")
        self.assertEqual(result["tables"]["income"], [{"ann_date": "20240429"}])

    def test_failure_preserves_diagnosis_and_redacts_credentials(self):
        token = "unit-test-placeholder-token"
        with patch.dict("os.environ", {"TUSHARE_TOKEN": token}), \
                patch("astock.providers.urllib.request.urlopen", side_effect=OSError("connection reset " + token)), \
                patch("astock.providers.time.sleep"), self.assertRaises(RuntimeError) as caught:
            request_json("https://api.tushare.pro")
        self.assertIn("connection reset", str(caught.exception))
        self.assertIn("[REDACTED]", str(caught.exception))
        self.assertNotIn(token, str(caught.exception))

    def test_missing_adjusted_field_never_silently_becomes_raw(self):
        payload = {"code": 0, "data": {"sh600519": {"day": [["2024-01-02", 10, 10, 11, 9, 100]]}}}
        with patch("astock.providers.request_json", return_value=payload), self.assertRaises(RuntimeError):
            history("600519", "2024-01-01", "2024-12-31", adjust="qfq")

    def test_source_mapping_and_volume_units(self):
        payload = {"code": 0, "data": {"sh600519": {"day": [["2024-01-02", 10, 10.5, 11, 9, 100]]}}}
        with patch("astock.providers.request_json", return_value=payload):
            rows, meta = history("600519", "2024-01-01", "2024-12-31")
        self.assertEqual(rows[0]["volume"], 10000)
        self.assertEqual(rows[0]["close"], 10.5)
        self.assertEqual(meta["price_mode"], "raw")
