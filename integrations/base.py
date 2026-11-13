"""Small, typed integration boundary. No user command strings are accepted."""
from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Protocol

from pydantic import BaseModel, Field


class AdapterResult(BaseModel):
    status: Literal['succeeded', 'failed']
    raw_output: Any = None
    normalized: dict = Field(default_factory=dict)
    provenance: dict = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
    error: dict | None = None


class Adapter(Protocol):
    id: str
    version: str
    capabilities: list[str]

    def validate_config(self, config: dict) -> dict: ...
    def health(self, config: dict) -> dict: ...
    def execute(self, input: dict, config: dict,
                cancelled: Callable[[], bool] = lambda: False) -> AdapterResult: ...


@dataclass(frozen=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str
    elapsed_ms: float


class ExecutionError(RuntimeError):
    """Contains only a controlled error code, never command output or secrets."""


def safe_run(argv: list[str], *, cwd: str | Path, env: dict[str, str] | None = None,
             timeout: float = 30, max_output: int = 2_000_000,
             cancelled: Callable[[], bool] = lambda: False) -> ProcessResult:
    """Execute a developer-selected binary with bounded output and no shell.

    argv[0] must be absolute. This helper is a process-control boundary, not a
    security sandbox. Production scanner workers must also use container CPU,
    memory, filesystem and network limits. Windows children are terminated via
    taskkill /T using a numeric process id; Linux children share a process group.
    """
    if not argv or not Path(argv[0]).is_absolute() or not Path(argv[0]).is_file():
        raise ValueError('A deployment-controlled absolute executable is required')
    if not 0 < timeout <= 300 or not 0 < max_output <= 10_000_000:
        raise ValueError('Invalid process limits')
    if cancelled():
        raise ExecutionError('cancelled')
    started = time.perf_counter()
    process = subprocess.Popen(argv, cwd=str(cwd), env=env, shell=False,
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=os.name != 'nt',
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    buffers: list[bytearray] = [bytearray(), bytearray()]
    exceeded = threading.Event()
    lock = threading.Lock()
    total = 0

    def read(stream, destination):
        nonlocal total
        while chunk := stream.read(4096):
            with lock:
                remaining = max(0, max_output - total)
                buffers[destination].extend(chunk[:remaining])
                total += len(chunk)
                if total > max_output:
                    exceeded.set()
        stream.close()

    readers = [threading.Thread(target=read, args=(process.stdout, 0), daemon=True),
               threading.Thread(target=read, args=(process.stderr, 1), daemon=True)]
    for reader in readers:
        reader.start()
    failure = None
    try:
        while process.poll() is None:
            if exceeded.is_set():
                failure = 'output_limit_exceeded'
            elif cancelled():
                failure = 'cancelled'
            elif time.perf_counter() - started > timeout:
                failure = 'timeout'
            if failure:
                break
            time.sleep(0.025)
    finally:
        if process.poll() is None:
            if os.name == 'nt':
                taskkill = Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32/taskkill.exe'
                subprocess.run([str(taskkill), '/PID', str(process.pid), '/T', '/F'],
                               shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.kill()
        process.wait(timeout=5)
        for reader in readers:
            reader.join(timeout=2)
    if exceeded.is_set():
        failure = failure or 'output_limit_exceeded'
    if failure:
        raise ExecutionError(failure)
    return ProcessResult(process.returncode, bytes(buffers[0]).decode('utf-8', errors='replace'),
                         bytes(buffers[1]).decode('utf-8', errors='replace'),
                         round((time.perf_counter()-started)*1000, 3))
