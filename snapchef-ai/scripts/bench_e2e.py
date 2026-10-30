"""End-to-end benchmark for SnapChef (real uvicorn + HTTP).

Measures cold start, warm p50/p95, and RSS. Run:
    uv run --with psutil python -m scripts.bench_e2e
"""

import ctypes
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

BASE_DIR = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
PORT = 8017
URL = f"http://{HOST}:{PORT}"


def find_worker_pid():
    try:
        import psutil

        for proc in psutil.process_iter(["pid", "cmdline", "memory_info"]):
            try:
                cmdline = " ".join(proc.info.get("cmdline") or [])
                if "uvicorn" in cmdline and "snapchef_ai.api:app" in cmdline:
                    rss = proc.info["memory_info"].rss
                    if rss > 50 * 1024 * 1024:
                        return proc.info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    return 0


def rss_bytes():
    try:
        import psutil

        pid = find_worker_pid()
        if pid:
            return psutil.Process(pid).memory_info().rss
    except Exception:
        pass
    return 0


def wait_for_health(timeout=60.0):
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        try:
            response = httpx.get(f"{URL}/health", timeout=2.0)
            if response.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise TimeoutError("server did not become healthy")


def main():
    with tempfile.TemporaryDirectory() as directory:
        from PIL import Image

        image_path = Path(directory) / "blank.png"
        Image.new("RGB", (224, 224), (240, 240, 240)).save(image_path, format="PNG")
        image_bytes = image_path.read_bytes()

        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "snapchef_ai.api:app",
                "--host",
                HOST,
                "--port",
                str(PORT),
                "--log-level",
                "warning",
            ],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Pin the worker to P-cores once it appears.
        for _ in range(50):
            pid = find_worker_pid()
            if pid:
                try:
                    handle = ctypes.windll.kernel32.OpenProcess(0x001F0FFF, False, pid)
                    if handle:
                        ctypes.windll.kernel32.SetProcessAffinityMask(handle, 0xFFF)
                        ctypes.windll.kernel32.SetPriorityClass(handle, 0x80)
                        ctypes.windll.kernel32.CloseHandle(handle)
                except Exception:
                    pass
                break
            time.sleep(0.2)

        try:
            wait_for_health()
            cold_start_begin = time.perf_counter()
            first = httpx.post(
                f"{URL}/api/predict",
                files={"file": ("blank.png", image_bytes, "image/png")},
                timeout=60.0,
            )
            cold_start = (time.perf_counter() - cold_start_begin) * 1000
            assert first.status_code == 200, first.text

            times = []
            rss_samples = []
            for _ in range(50):
                sample_begin = time.perf_counter()
                response = httpx.post(
                    f"{URL}/api/predict",
                    files={"file": ("blank.png", image_bytes, "image/png")},
                    timeout=60.0,
                )
                times.append((time.perf_counter() - sample_begin) * 1000)
                assert response.status_code == 200, response.text
                rss_samples.append(rss_bytes())
                time.sleep(0.05)

            times.sort()
            rss_samples = [value for value in rss_samples if value]
            print("cold start (first /api/predict): %.1f ms" % cold_start)
            print("warm p50: %.1f ms" % statistics.median(times))
            print("warm p95: %.1f ms" % times[47])
            print("warm max: %.1f ms" % times[-1])
            if rss_samples:
                print("RSS min: %.1f MB" % (min(rss_samples) / 1024 / 1024))
                print("RSS max: %.1f MB" % (max(rss_samples) / 1024 / 1024))

            rec_times = []
            for _ in range(20):
                sample_begin = time.perf_counter()
                response = httpx.post(
                    f"{URL}/api/recommend",
                    json={"ingredients": ["apple", "banana"], "limit": 5},
                    timeout=60.0,
                )
                rec_times.append((time.perf_counter() - sample_begin) * 1000)
                assert response.status_code == 200, response.text
            rec_times.sort()
            print("recommend p50: %.1f ms" % statistics.median(rec_times))
            print("recommend p95: %.1f ms" % rec_times[18])
        finally:
            server.terminate()
            server.wait(timeout=30)


if __name__ == "__main__":
    main()
