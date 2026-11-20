import time
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from radar.models import JobPosting
from radar.storage import JobStorage
from radar.adapters import (
    KocPortalAdapter,
    TrendyolPortalAdapter,
    DefensePortalAdapter,
    AkbankPortalAdapter,
    IsBankasiPortalAdapter,
    ThyPortalAdapter,
    BaykarPortalAdapter,
    CorporateAtsAdapter,
    CorporateGuestAdapter
)


class JobAggregator:
    def __init__(self, storage: Optional[JobStorage] = None):
        self.storage = storage or JobStorage()

    def get_all_adapters(self) -> List[Any]:
        # Custom user-added targets
        custom_targets = self.storage.get_tracked_targets()

        return [
            KocPortalAdapter(),
            TrendyolPortalAdapter(),
            DefensePortalAdapter(),
            AkbankPortalAdapter(),
            IsBankasiPortalAdapter(),
            ThyPortalAdapter(),
            BaykarPortalAdapter(),
            CorporateAtsAdapter(),
            CorporateGuestAdapter(custom_targets=custom_targets)
        ]

    def run_all(self, on_progress: Optional[Callable[[str, int], None]] = None) -> Dict[str, Any]:
        """
        Tüm resmi portalları ve kurumsal kaynakları eşzamanlı olarak tarar,
        veritabanına yazar ve özet istatistik döner.
        """
        start_time = time.time()
        adapters = self.get_all_adapters()
        total_fetched = 0
        all_postings: List[JobPosting] = []
        adapter_results: Dict[str, int] = {}

        def _run_single(adapter):
            name = getattr(adapter, "name", adapter.__class__.__name__)
            try:
                jobs = adapter.fetch_jobs()
                return name, jobs
            except Exception as e:
                print(f"[{name}] Tarama hatası: {e}")
                return name, []

        with ThreadPoolExecutor(max_workers=len(adapters)) as executor:
            future_to_adapter = {executor.submit(_run_single, a): a for a in adapters}
            for future in as_completed(future_to_adapter):
                name, jobs = future.result()
                adapter_results[name] = len(jobs)
                all_postings.extend(jobs)
                if on_progress:
                    on_progress(name, len(jobs))

        # Veritabanına toplu kayıt ve yeni ilan tespiti
        new_count, updated_count = self.storage.save_jobs_batch(all_postings)
        elapsed = round(time.time() - start_time, 2)

        return {
            "elapsed_seconds": elapsed,
            "total_fetched": len(all_postings),
            "new_jobs": new_count,
            "updated_jobs": updated_count,
            "adapter_breakdown": adapter_results,
            "overall_stats": self.storage.get_stats()
        }

    def scan_single_target(self, keyword: str, sector: str = "other") -> List[JobPosting]:
        """
        Kullanıcının eklediği özel bir şirketi anında tarar.
        """
        self.storage.add_tracked_target(keyword, sector)
        adapter = CorporateGuestAdapter(
            custom_targets=[{"keyword": keyword, "sector": sector}],
            custom_only=True
        )
        jobs = adapter.fetch_jobs()
        self.storage.save_jobs_batch(jobs)
        return jobs
