import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import LogEvent


class LogStore:
    def __init__(self, jobs_dir: Path):
        self.jobs_dir = Path(jobs_dir)
        self.logs_dir = self.jobs_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _log_file(self, job_id: str) -> Path:
        return self.logs_dir / f"{job_id}.jsonl"

    def append(self, job_id: str, event: LogEvent) -> None:
        log_file = self._log_file(job_id)
        with open(log_file, "a") as f:
            f.write(event.model_dump_json() + "\n")

    def get_all(self, job_id: str) -> list[LogEvent]:
        log_file = self._log_file(job_id)
        if not log_file.exists():
            return []
        
        events = []
        with open(log_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        events.append(LogEvent(**data))
                    except (json.JSONDecodeError, ValueError):
                        pass
        return events

    def delete(self, job_id: str) -> None:
        log_file = self._log_file(job_id)
        if log_file.exists():
            log_file.unlink()
