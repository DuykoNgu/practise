from datetime import datetime

from app.core.database import DatabaseUnavailableError


class FakeHealthProbe:
    def __init__(self, last_job_at: datetime | None = None, available: bool = True) -> None:
        self.last_job_at = last_job_at
        self.available = available

    def last_job_finished_at(self) -> datetime | None:
        if not self.available:
            raise DatabaseUnavailableError()
        return self.last_job_at
