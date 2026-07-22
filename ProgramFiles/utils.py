# utils.py
"""Yardimci fonksiyonlar"""

import os
import sys
import logging
import subprocess
import platform
from datetime import datetime, timedelta
import requests
from config import LOG_FILE, TEST_URLS, APP_DATA_DIR, VERSION_CHECK_URL, APP_VERSION


# --- LOG SISTEMI ---
def setup_logger():
    logger = logging.getLogger("DPIApp")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger


logger = setup_logger()


def log_info(msg: str):
    logger.info(msg)


def log_error(msg: str):
    logger.error(msg)


def log_debug(msg: str):
    logger.debug(msg)


def get_log_content(lines: int = 100) -> str:
    """Log dosyasindan son satirlari okur"""
    try:
        if not os.path.exists(LOG_FILE):
            return "[Log dosyasi bulunamadi]"
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:]
            return "".join(last_lines)
    except Exception as e:
        return f"[Log okuma hatasi: {e}]"


def clear_logs():
    """Log dosyasini temizler"""
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")
        log_info("Log temizlendi")
        return True
    except Exception as e:
        log_error(f"Log temizleme hatasi: {e}")
        return False


# --- NETWORK TEST ---
def test_connection(url: str = None, timeout: int = 5) -> dict:
    """Belirtilen URL'e baglanti testi yapar, detayli sonuc doner"""
    test_url = url or TEST_URLS[0]
    result = {
        "url": test_url,
        "success": False,
        "status_code": None,
        "latency_ms": None,
        "error": None
    }
    try:
        start = datetime.now()
        r = requests.get(test_url, timeout=timeout, allow_redirects=True)
        elapsed = (datetime.now() - start).total_seconds() * 1000
        result["success"] = r.status_code == 200
        result["status_code"] = r.status_code
        result["latency_ms"] = round(elapsed, 1)
    except requests.Timeout:
        result["error"] = "Zaman asimi"
    except requests.ConnectionError:
        result["error"] = "Baglanti hatasi"
    except Exception as e:
        result["error"] = str(e)
    return result


def test_all_connections(timeout: int = 5) -> dict:
    """Tum test URL'lerini kontrol eder"""
    results = {}
    for url in TEST_URLS:
        results[url] = test_connection(url, timeout)
    return results


def get_connection_status() -> tuple:
    """Genel baglanti durumu"""
    results = test_all_connections(timeout=4)
    passed = sum(1 for r in results.values() if r["success"])
    total = len(results)

    if passed == total:
        return (True, f"Tum siteler erisilebilir ({passed}/{total})", results)
    elif passed > 0:
        return (True, f"Kismi erisim ({passed}/{total} site acik)", results)
    else:
        return (False, "Hicbir siteye erisilemiyor", results)


def measure_latency(host: str = "8.8.8.8", count: int = 3) -> dict:
    """Ping gecikmesini olcer"""
    result = {"host": host, "avg_ms": None, "packet_loss": 100, "error": None}
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        cmd = ["ping", param, str(count), host]
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW
        )
        output = out.stdout + out.stderr

        if "time=" in output or "time<" in output:
            import re
            times = re.findall(r"time[=<>](\d+\.?\d*)", output)
            if times:
                nums = [float(t) for t in times]
                result["avg_ms"] = round(sum(nums) / len(nums), 1)
        if "Lost = 0" in output or "0% loss" in output or "0 received" not in output:
            result["packet_loss"] = 0
    except Exception as e:
        result["error"] = str(e)
    return result


# --- GUNCELLEME KONTROL ---
def check_for_updates() -> dict:
    """GitHub'dan son surumu kontrol eder"""
    result = {
        "has_update": False,
        "latest_version": None,
        "download_url": None,
        "error": None
    }
    try:
        r = requests.get(VERSION_CHECK_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        latest_tag = data.get("tag_name", "").lstrip("v")
        if latest_tag and latest_tag > APP_VERSION:
            result["has_update"] = True
            result["latest_version"] = latest_tag
            if data.get("assets"):
                result["download_url"] = data["assets"][0].get("browser_download_url")
        result["latest_version"] = latest_tag or data.get("tag_name", "bilinmiyor")
    except Exception as e:
        result["error"] = str(e)
    return result


# --- SISTEM BILGISI ---
def get_system_info() -> dict:
    """Sistem bilgilerini toplar"""
    info = {
        "is_admin": False,
        "os_version": platform.version(),
        "os_release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version.split()[0],
        "app_version": APP_VERSION,
        "app_data_dir": APP_DATA_DIR
    }
    try:
        import ctypes
        info["is_admin"] = bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        pass
    return info


def get_public_ip() -> str:
    """Genel IP adresini alir"""
    try:
        r = requests.get("https://api.ipify.org", timeout=5)
        return r.text.strip()
    except Exception:
        return "Alinamadi"


# --- DOSYA YARDIMCILARI ---
def get_file_size_mb(filepath: str) -> float:
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0.0


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)
