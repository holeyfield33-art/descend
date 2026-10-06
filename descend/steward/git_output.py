"""Bounded cross-platform Git pipe capture, without echoing private stderr."""
from __future__ import annotations

import os
import queue
import signal
import subprocess
import threading
import time


def capture_git(argv: list[str], *, env: dict[str, str], timeout: float = 20, max_output: int = 2097152) -> bytes:
    process = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=os.name == "posix")
    chunks = queue.Queue(maxsize=16)
    stop = threading.Event()
    def read(stream, name):
        try:
            while not stop.is_set():
                data = stream.read(4096)
                while not stop.is_set():
                    try:
                        chunks.put((name, data), timeout=0.1)
                        break
                    except queue.Full:
                        pass
                if not data:
                    break
        except (OSError, ValueError):
            pass
    threads = [threading.Thread(target=read, args=(stream, name), daemon=True)
               for stream, name in [(process.stdout, "stdout"), (process.stderr, "stderr")]]
    for thread in threads:
        thread.start()
    remaining_streams, total = 2, 0
    output = bytearray()
    deadline = time.monotonic() + timeout
    try:
        while remaining_streams:
            left = deadline-time.monotonic()
            if left <= 0:
                raise RuntimeError("Git deadline exceeded")
            try:
                name, data = chunks.get(timeout=left)
            except queue.Empty:
                raise RuntimeError("Git deadline exceeded") from None
            if not data:
                remaining_streams -= 1
                continue
            total += len(data)
            if total > max_output:
                raise RuntimeError("Git output cap exceeded")
            if name == "stdout":
                output.extend(data)
        process.wait(timeout=max(0.01, deadline-time.monotonic()))
        if process.returncode != 0:
            raise RuntimeError("Git read failed")
        return bytes(output)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git deadline exceeded") from None
    finally:
        stop.set()
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif process.poll() is None:
            process.kill()
        process.wait()
        for stream in (process.stdout, process.stderr):
            stream.close()
        for thread in threads:
            thread.join(timeout=1)
