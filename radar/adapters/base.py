from abc import ABC, abstractmethod
from typing import List
from radar.models import JobPosting


class BaseJobAdapter(ABC):
    name: str = "BaseAdapter"
    sector: str = "other"

    @abstractmethod
    def fetch_jobs(self) -> List[JobPosting]:
        """
        Şirketin resmi web sitesinden / API'sinden ilanları çeker
        ve standart JobPosting nesneleri listesi döner.
        """
        pass
