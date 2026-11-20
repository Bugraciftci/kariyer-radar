import unittest
import os
import sys
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from radar.models import JobPosting
from radar.storage import JobStorage
from radar.adapters import (
    KocPortalAdapter,
    TrendyolPortalAdapter,
    DefensePortalAdapter,
    AkbankPortalAdapter,
    IsBankasiPortalAdapter,
    ThyPortalAdapter
)


class TestJobModelAndStorage(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.storage = JobStorage(db_path=self.temp_db.name)

    def tearDown(self):
        try:
            os.remove(self.temp_db.name)
        except Exception:
            pass

    def test_save_and_retrieve_job(self):
        job = JobPosting(
            id="test-123",
            company="Test Şirketi",
            sector="tech",
            title="Senior iOS Developer",
            location="İstanbul (Hibrit)",
            work_model="Tam Zamanlı",
            description_text="Swift ve SwiftUI ile iOS geliştirme.",
            requirements=["Swift", "SwiftUI", "Combine"],
            apply_url="https://example.com/apply"
        )

        is_new = self.storage.save_job(job)
        self.assertTrue(is_new)

        # Retrieval
        retrieved = self.storage.get_job_by_id("test-123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.company, "Test Şirketi")
        self.assertEqual(retrieved.title, "Senior iOS Developer")
        self.assertIn("SwiftUI", retrieved.requirements)

        # Duplicate save check
        is_new_again = self.storage.save_job(job)
        self.assertFalse(is_new_again)

    def test_search_and_filter(self):
        j1 = JobPosting(id="1", company="Trendyol", sector="tech", title="iOS Developer")
        j2 = JobPosting(id="2", company="Akbank", sector="bank", title="Müfettiş Yardımcısı")
        self.storage.save_jobs_batch([j1, j2])

        bank_jobs = self.storage.get_jobs(sector="bank")
        self.assertEqual(len(bank_jobs), 1)
        self.assertEqual(bank_jobs[0].company, "Akbank")

        search_jobs = self.storage.get_jobs(search="iOS")
        self.assertEqual(len(search_jobs), 1)
        self.assertEqual(search_jobs[0].company, "Trendyol")


class TestLiveAdapters(unittest.TestCase):
    def test_trendyol_adapter(self):
        adapter = TrendyolPortalAdapter()
        jobs = adapter.fetch_jobs()
        self.assertGreater(len(jobs), 5)
        self.assertEqual(jobs[0].company, "Trendyol")
        self.assertEqual(jobs[0].sector, "tech")

    def test_defense_adapter(self):
        adapter = DefensePortalAdapter()
        jobs = adapter.fetch_jobs()
        self.assertGreater(len(jobs), 5)
        self.assertEqual(jobs[0].sector, "defense")

    def test_akbank_adapter(self):
        adapter = AkbankPortalAdapter()
        jobs = adapter.fetch_jobs()
        self.assertGreater(len(jobs), 5)
        self.assertEqual(jobs[0].company, "Akbank")
        self.assertEqual(jobs[0].sector, "bank")

    def test_koc_adapter(self):
        adapter = KocPortalAdapter()
        jobs = adapter.fetch_jobs()
        self.assertGreater(len(jobs), 5)
        self.assertEqual(jobs[0].sector, "koc")


if __name__ == "__main__":
    unittest.main()
