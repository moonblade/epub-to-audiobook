import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from models import JobState, JobStatus


class JobManager:
    def __init__(self, jobs_dir: Path):
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def _job_file(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.json"

    def create_job(
        self,
        job_id: str,
        epub_path: str,
        epub_filename: str,
        output_dir: str,
        voice: str = "am_adam",
    ) -> JobState:
        job = JobState(
            job_id=job_id,
            epub_path=epub_path,
            epub_filename=epub_filename,
            output_dir=output_dir,
            voice=voice,
            status=JobStatus.PENDING,
        )
        self._save_job(job)
        return job

    def get_job(self, job_id: str) -> Optional[JobState]:
        job_file = self._job_file(job_id)
        if not job_file.exists():
            return None
        with open(job_file, "r") as f:
            data = json.load(f)
        return JobState(**data)

    def update_job(self, job_id: str, **kwargs) -> Optional[JobState]:
        job = self.get_job(job_id)
        if not job:
            return None
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        job.updated_at = datetime.now()
        self._save_job(job)
        return job

    def update_checkpoint(
        self,
        job_id: str,
        chapter: int,
        chunk: int,
        total_chapters: int = 0,
        total_chunks: int = 0,
    ) -> Optional[JobState]:
        job = self.get_job(job_id)
        if not job:
            return None
        job.current_chapter = chapter
        job.current_chunk = chunk
        if total_chapters > 0:
            job.total_chapters = total_chapters
        if total_chunks > 0:
            job.total_chunks = total_chunks
        if job.total_chunks > 0:
            job.progress = (chunk / job.total_chunks) * 100
        job.updated_at = datetime.now()
        self._save_job(job)
        return job

    def list_jobs(self) -> list[JobState]:
        jobs = []
        for job_file in self.jobs_dir.glob("*.json"):
            with open(job_file, "r") as f:
                data = json.load(f)
            jobs.append(JobState(**data))
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def delete_job(self, job_id: str) -> bool:
        job_file = self._job_file(job_id)
        if job_file.exists():
            job_file.unlink()
            return True
        return False

    def _save_job(self, job: JobState) -> None:
        job_file = self._job_file(job.job_id)
        with open(job_file, "w") as f:
            json.dump(job.model_dump(mode="json"), f, indent=2, default=str)
