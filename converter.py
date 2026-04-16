import asyncio
import os
import shutil
import urllib.request
from pathlib import Path
from threading import Event
from typing import Optional

import numpy as np
import soundfile as sf
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from kokoro_onnx import Kokoro

from config import MODEL_FILE, VOICES_FILE, MODEL_URL, VOICES_URL, MODELS_PATH
from models import JobState, JobStatus, LogEvent
from job_manager import JobManager


def download_models() -> bool:
    MODELS_PATH.mkdir(parents=True, exist_ok=True)
    
    for file_path, url in [(MODEL_FILE, MODEL_URL), (VOICES_FILE, VOICES_URL)]:
        if not file_path.exists():
            print(f"Downloading {file_path.name}...")
            try:
                urllib.request.urlretrieve(url, file_path)
                print(f"Downloaded {file_path.name}")
            except Exception as e:
                print(f"Failed to download {file_path.name}: {e}")
                return False
    return True


def extract_chapters_from_epub(epub_path: str) -> list[dict[str, str | int]]:
    book = epub.read_epub(epub_path)
    chapters = []
    
    for item in book.get_items():
        if item.get_type() == ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_body_content(), "html.parser")
            text = soup.get_text().strip()
            if len(text) > 50:
                title_tag = soup.find(["h1", "h2", "h3", "title"])
                title = title_tag.get_text().strip() if title_tag else f"Chapter {len(chapters) + 1}"
                chapters.append({
                    "title": title,
                    "content": text,
                    "order": len(chapters) + 1
                })
    
    return chapters


def chunk_text(text: str, max_size: int = 1000) -> list[str]:
    sentences = text.replace('\n', ' ').split('.')
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        sentence = sentence + '.'
        sentence_size = len(sentence)
        
        if sentence_size > max_size:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            words = sentence.split()
            piece = []
            piece_size = 0
            for word in words:
                if piece_size + len(word) + 1 > max_size:
                    if piece:
                        chunks.append(' '.join(piece))
                    piece = [word]
                    piece_size = len(word)
                else:
                    piece.append(word)
                    piece_size += len(word) + 1
            if piece:
                chunks.append(' '.join(piece))
            continue
        
        if current_size + sentence_size > max_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_size = 0
        
        current_chunk.append(sentence)
        current_size += sentence_size
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


class ConversionJob:
    def __init__(
        self,
        job_state: JobState,
        job_manager: JobManager,
        log_queue: asyncio.Queue[LogEvent],
    ):
        self.job_state = job_state
        self.job_manager = job_manager
        self.log_queue = log_queue
        self.should_stop = Event()
        self.kokoro: Optional[Kokoro] = None

    def _emit_log(self, level: str, message: str, progress: float = 0.0, chapter: Optional[int] = None, chunk: Optional[int] = None):
        event = LogEvent(
            level=level,
            message=message,
            progress=progress,
            chapter=chapter,
            chunk=chunk,
        )
        try:
            self.log_queue.put_nowait(event)
        except asyncio.QueueFull:
            pass

    def _init_kokoro(self) -> bool:
        if not MODEL_FILE.exists() or not VOICES_FILE.exists():
            self._emit_log("info", "Downloading TTS models (this may take a few minutes)...")
            if not download_models():
                self._emit_log("error", "Failed to download models")
                return False
            self._emit_log("info", "Models downloaded successfully")
        
        try:
            self.kokoro = Kokoro(str(MODEL_FILE), str(VOICES_FILE))
            return True
        except Exception as e:
            self._emit_log("error", f"Failed to initialize Kokoro: {e}")
            return False

    def run(self) -> None:
        job_id = self.job_state.job_id
        output_dir = Path(self.job_state.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.job_manager.update_job(job_id, status=JobStatus.RUNNING)
        self._emit_log("info", "Starting conversion...")
        
        if not self._init_kokoro():
            self.job_manager.update_job(job_id, status=JobStatus.FAILED, error="Failed to initialize TTS")
            return
        
        try:
            chapters = extract_chapters_from_epub(self.job_state.epub_path)
            if not chapters:
                self._emit_log("error", "No chapters found in EPUB")
                self.job_manager.update_job(job_id, status=JobStatus.FAILED, error="No chapters found")
                return
            
            all_chunks = []
            for chapter in chapters:
                chapter_chunks = chunk_text(str(chapter["content"]))
                for chunk in chapter_chunks:
                    all_chunks.append({"chapter": chapter["order"], "title": chapter["title"], "text": chunk})
            
            total_chunks = len(all_chunks)
            self.job_manager.update_checkpoint(job_id, 0, 0, len(chapters), total_chunks)
            self._emit_log("info", f"Found {len(chapters)} chapters, {total_chunks} chunks")
            
            start_chunk = self.job_state.current_chunk
            chapter_audio: dict[int, list[float]] = {}
            sample_rate = 24000
            
            for i, chunk_data in enumerate(all_chunks):
                if i < start_chunk:
                    continue
                
                if self.should_stop.is_set():
                    self._emit_log("info", "Conversion paused")
                    self.job_manager.update_job(job_id, status=JobStatus.PAUSED)
                    return
                
                chapter_num = chunk_data["chapter"]
                progress = ((i + 1) / total_chunks) * 100
                
                self._emit_log(
                    "info",
                    f"Processing chunk {i + 1}/{total_chunks} (Chapter {chapter_num})",
                    progress=progress,
                    chapter=chapter_num,
                    chunk=i + 1,
                )
                
                try:
                    voice = self.job_state.voice
                    lang = "en-gb" if voice.startswith("b") else "en-us"
                    if self.kokoro is None:
                        raise RuntimeError("Kokoro not initialized")
                    samples, sr = self.kokoro.create(
                        chunk_data["text"],
                        voice=voice,
                        speed=1.0,
                        lang=lang,
                    )
                    sample_rate = sr
                    
                    if chapter_num not in chapter_audio:
                        chapter_audio[chapter_num] = []
                    chapter_audio[chapter_num].extend(samples)
                    
                except Exception as e:
                    self._emit_log("warning", f"Failed to process chunk {i + 1}: {e}")
                
                self.job_manager.update_checkpoint(job_id, chapter_num, i + 1, len(chapters), total_chunks)
            
            self._emit_log("info", "Saving audio files...")
            all_samples = []
            
            for chapter_num in sorted(chapter_audio.keys()):
                samples = chapter_audio[chapter_num]
                chapter_file = output_dir / f"chapter_{chapter_num:03d}.wav"
                sf.write(str(chapter_file), np.array(samples), sample_rate)
                all_samples.extend(samples)
                self._emit_log("info", f"Saved {chapter_file.name}")
            
            if all_samples:
                full_file = output_dir / "full.wav"
                sf.write(str(full_file), np.array(all_samples), sample_rate)
                self._emit_log("info", f"Saved {full_file.name}")
            
            self.job_manager.update_job(job_id, status=JobStatus.COMPLETED, progress=100.0)
            self._emit_log("info", "Conversion completed!", progress=100.0)
            
        except Exception as e:
            self._emit_log("error", f"Conversion failed: {e}")
            self.job_manager.update_job(job_id, status=JobStatus.FAILED, error=str(e))

    def stop(self) -> None:
        self.should_stop.set()
