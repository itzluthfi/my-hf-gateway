"""
services/queue_service.py — Global Queue & Concurrency Manager for Heavy Tasks
"""
import asyncio
import time
from typing import Callable, Coroutine, Any

# Maksimal task berat yang boleh berjalan secara bersamaan (misal 2 render/browse bersamaan)
MAX_CONCURRENT_HEAVY_JOBS = 2

# Semaphore untuk membatasi eksekusi paralel
_heavy_semaphore = asyncio.Semaphore(MAX_CONCURRENT_HEAVY_JOBS)

# Counter dan list antrean
_waiting_count = 0
_lock = asyncio.Lock()


async def run_in_queue(
    on_queue_update: Callable[[int, int], Coroutine[Any, Any, None]],
    job_coroutine_fn: Callable[[], Coroutine[Any, Any, Any]],
    estimated_job_seconds: int = 25
) -> Any:
    """
    Menjalankan job di dalam antrean berurutan (FIFO).
    Memberikan feedback posisi nomor antrean dan estimasi waktu tunggu.
    """
    global _waiting_count
    
    # 1. Cek apakah harus menunggu di antrean
    async with _lock:
        _waiting_count += 1
        pos = _waiting_count
        
    if pos > MAX_CONCURRENT_HEAVY_JOBS:
        # User harus mengantre
        wait_pos = pos - MAX_CONCURRENT_HEAVY_JOBS
        est_sec = wait_pos * estimated_job_seconds
        try:
            await on_queue_update(wait_pos, est_sec)
        except Exception:
            pass

    # 2. Menunggu giliran semaphore
    await _heavy_semaphore.acquire()
    
    try:
        async with _lock:
            _waiting_count -= 1
        
        # 3. Jalankan tugas utama
        result = await job_coroutine_fn()
        return result
    finally:
        _heavy_semaphore.release()
