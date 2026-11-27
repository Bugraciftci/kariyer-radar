import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from radar.models import JobPosting
from radar.storage import JobStorage


class TestStorageEdgeCases(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.storage = JobStorage(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_batch_deduplication_and_empty_search(self):
        jobs = [
            JobPosting(id="dup-1", company="Baykar", sector="defense", title="Flight Software Engineer"),
            JobPosting(id="dup-1", company="Baykar", sector="defense", title="Flight Software Engineer"),
            JobPosting(id="uniq-2", company="THY", sector="aviation", title="Mobile Engineer"),
        ]
        self.storage.save_jobs_batch(jobs)
        all_jobs = self.storage.get_jobs()
        self.assertEqual(len(all_jobs), 2)

        missing = self.storage.get_jobs(search="nonexistent-xyz-token")
        self.assertEqual(missing, [])

    def test_sector_and_company_filter_isolation(self):
        self.storage.save_jobs_batch([
            JobPosting(id="s-1", company="Akbank", sector="bank", title="iOS Developer"),
            JobPosting(id="s-2", company="Trendyol", sector="tech", title="iOS Developer"),
        ])
        tech_ios = self.storage.get_jobs(sector="tech", search="iOS")
        self.assertEqual(len(tech_ios), 1)
        self.assertEqual(tech_ios[0].id, "s-2")


if __name__ == "__main__":
    unittest.main()
