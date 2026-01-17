# utils.py
"""Yardımcı fonksiyonlar"""

import os
import logging
from datetime import datetime
import requests
from config import LOG_FILE, TEST_URLS

# --- LOG SİSTEMİ ---
def setup_logger():
    """Basit dosya tabanlı logger"""
    logger = logging.getLogger("DPIApp")
    logger.setLevel(logging.DEBUG)
    
    # Dosya handler
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    
    # Format
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


# --- NETWORK TEST ---
def test_connection(url: str = None, timeout: int = 5) -> bool:
    """Belirtilen URL'e bağlantı testi yapar"""
    test_url = url or TEST_URLS[0]
    try:
        r = requests.get(test_url, timeout=timeout, allow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False

def test_all_connections(timeout: int = 5) -> dict:
    """Tüm test URL'lerini kontrol eder"""
    results = {}
    for url in TEST_URLS:
        results[url] = test_connection(url, timeout)
    return results

def get_connection_status() -> tuple[bool, str]:
    """
    Genel bağlantı durumunu döndürür
    Returns: (success: bool, message: str)
    """
    results = test_all_connections(timeout=4)
    passed = sum(results.values())
    total = len(results)
    
    if passed == total:
        return True, f"Tüm siteler erişilebilir ({passed}/{total})"
    elif passed > 0:
        return True, f"Kısmi erişim ({passed}/{total} site açık)"
    else:
        return False, "Hiçbir siteye erişilemiyor"


# --- DOSYA YARDIMCILARI ---
def get_file_size_mb(filepath: str) -> float:
    """Dosya boyutunu MB cinsinden döndürür"""
    if os.path.exists(filepath):
        return os.path.getsize(filepath) / (1024 * 1024)
    return 0.0

def ensure_dir(path: str):
    """Klasör yoksa oluşturur"""
    os.makedirs(path, exist_ok=True)