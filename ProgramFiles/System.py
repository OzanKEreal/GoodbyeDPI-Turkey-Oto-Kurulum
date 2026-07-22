# System.py
"""Cekirdek is mantigi - Download, Process, Registry, Monitor"""

import os
import sys
import ctypes
import json
import zipfile
import subprocess
import threading
import time
import socket
import platform
from datetime import datetime
from typing import Callable, Optional
import requests
import winreg

from config import (
    GITHUB_URL, FOLDER_NAME, CONFIG_FILE,
    APP_NAME_REG, CMD_PROFILES, APP_DATA_DIR,
    DPI_WAIT_AFTER_START, MONITOR_INTERVAL,
    AUTO_RECONNECT_DELAY, MONITOR_URLS
)
from utils import log_info, log_error, log_debug, ensure_dir, test_connection


class DPIService:
    """GoodbyeDPI servis yoneticisi"""

    def __init__(self):
        self.github_url = GITHUB_URL
        self.folder_name = FOLDER_NAME
        self.config_file = CONFIG_FILE
        self.extract_path = os.path.join(self._get_base_dir(), self.folder_name)
        self.process = None
        self._config_cache = None
        self._monitor_active = False
        self._monitor_thread = None
        self._on_status_change = None
        self._uptime_start = None

        ensure_dir(APP_DATA_DIR)
        log_info("DPIService baslatildi")

    def _get_base_dir(self) -> str:
        """Calisma dizinini belirler (exe veya py)"""
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.getcwd()

    # ==================== ADMIN ====================
    @staticmethod
    def is_admin() -> bool:
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    @staticmethod
    def restart_as_admin():
        log_info("Admin olarak yeniden baslatiliyor...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

    # ==================== CONFIG ====================
    def load_config(self) -> dict:
        if self._config_cache:
            return self._config_cache

        default = {
            "working_cmd": None,
            "theme": "Dark",
            "auto_start": False,
            "auto_test": True,
            "minimize_to_tray": False,
            "auto_reconnect": True,
            "last_run": None,
            "favorite_profiles": [],
            "last_profile": None
        }

        if not os.path.exists(self.config_file):
            return default

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, val in default.items():
                    if key not in data:
                        data[key] = val
                self._config_cache = data
                return data
        except Exception as e:
            log_error(f"Config okuma hatasi: {e}")
            return default

    def save_config(self, **kwargs):
        config = self.load_config()
        config.update(kwargs)

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self._config_cache = config
            log_info(f"Config kaydedildi: {kwargs}")
        except Exception as e:
            log_error(f"Config kaydetme hatasi: {e}")

    def get_working_cmd(self) -> Optional[str]:
        return self.load_config().get("working_cmd")

    def set_working_cmd(self, cmd_file: str):
        self.save_config(working_cmd=cmd_file)

    def get_favorites(self) -> list:
        return self.load_config().get("favorite_profiles", [])

    def toggle_favorite(self, cmd_file: str) -> bool:
        favs = self.get_favorites()
        if cmd_file in favs:
            favs.remove(cmd_file)
            self.save_config(favorite_profiles=favs)
            return False
        else:
            favs.append(cmd_file)
            self.save_config(favorite_profiles=favs)
            return True

    def is_favorite(self, cmd_file: str) -> bool:
        return cmd_file in self.get_favorites()

    # ==================== STARTUP (REGISTRY) ====================
    def check_startup_status(self) -> bool:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            winreg.QueryValueEx(key, APP_NAME_REG)
            winreg.CloseKey(key)
            return True
        except OSError:
            return False

    def set_startup(self, enabled: bool) -> bool:
        if not getattr(sys, "frozen", False):
            log_debug("Dev modda startup atlandi")
            return False

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_ALL_ACCESS
            )

            if enabled:
                exe_path = f'"{sys.executable}"'
                winreg.SetValueEx(key, APP_NAME_REG, 0, winreg.REG_SZ, exe_path)
                log_info("Startup eklendi")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME_REG)
                    log_info("Startup kaldirildi")
                except OSError:
                    pass

            winreg.CloseKey(key)
            self.save_config(auto_start=enabled)
            return True

        except Exception as e:
            log_error(f"Startup ayarlama hatasi: {e}")
            return False

    # ==================== DOWNLOAD & EXTRACT ====================
    def download_and_extract(
        self,
        progress_cb: Callable[[int], None] = None,
        status_cb: Callable[[str], None] = None
    ) -> bool:
        try:
            ensure_dir(self.folder_name)
            zip_path = os.path.join(self.folder_name, "temp.zip")

            if status_cb:
                status_cb("Baglanti kuruluyor...")

            r = requests.get(self.github_url, stream=True, timeout=60)
            r.raise_for_status()

            total_size = int(r.headers.get("content-length", 0))
            downloaded = 0

            if status_cb:
                status_cb("Dosyalar indiriliyor...")

            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_cb and total_size > 0:
                            pct = int((downloaded / total_size) * 50)
                            progress_cb(pct)

            if status_cb:
                status_cb("Dosyalar cikartiliyor...")

            with zipfile.ZipFile(zip_path, "r") as z:
                files = z.namelist()
                for i, file in enumerate(files):
                    z.extract(file, self.folder_name)
                    if progress_cb:
                        pct = 50 + int((i / len(files)) * 50)
                        progress_cb(pct)

            os.remove(zip_path)

            if progress_cb:
                progress_cb(100)
            if status_cb:
                status_cb("Tamamlandi!")

            log_info("Download ve extract basarili")
            return True

        except Exception as e:
            log_error(f"Download/extract hatasi: {e}")
            if status_cb:
                status_cb(f"Hata: {e}")
            return False

    # ==================== PROCESS MANAGEMENT ====================
    def clean_process(self):
        try:
            subprocess.run(
                "taskkill /F /IM goodbyedpi.exe /T",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.process = None
            self._uptime_start = None
            log_debug("Process temizlendi")
        except Exception as e:
            log_error(f"Process temizleme hatasi: {e}")

    def _find_cmd_path(self, cmd_file: str) -> Optional[str]:
        for root, _, files in os.walk(self.extract_path):
            if cmd_file in files:
                return os.path.join(root, cmd_file)
        return None

    def start_dpi_process(self, cmd_file: str) -> bool:
        full_path = self._find_cmd_path(cmd_file)

        if not full_path:
            log_error(f"CMD bulunamadi: {cmd_file}")
            return False

        try:
            target_dir = os.path.dirname(full_path)

            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE

            self.process = subprocess.Popen(
                [full_path],
                cwd=target_dir,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=si,
                shell=True
            )

            self._uptime_start = datetime.now()
            log_info(f"DPI baslatildi: {cmd_file}")
            return True

        except Exception as e:
            log_error(f"DPI baslatma hatasi: {e}")
            return False

    def restart_dpi(self, cmd_file: str = None) -> bool:
        """Mevcut profili veya belirtilen profili yeniden baslatir"""
        if not cmd_file:
            cmd_file = self.get_working_cmd()
        if not cmd_file:
            return False
        self.clean_process()
        time.sleep(1)
        return self.start_dpi_process(cmd_file)

    def is_running(self) -> bool:
        if self.process is not None and self.process.poll() is None:
            return True
        return self._check_process_running()

    @staticmethod
    def _check_process_running() -> bool:
        """Sistemde goodbyedpi.exe calisiyor mu kontrol eder"""
        try:
            out = subprocess.run(
                "tasklist /FI \"IMAGENAME eq goodbyedpi.exe\" /NH",
                shell=True, capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return "goodbyedpi.exe" in out.stdout
        except Exception:
            return False

    def get_uptime(self) -> Optional[str]:
        if not self._uptime_start or not self.is_running():
            return None
        delta = datetime.now() - self._uptime_start
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{h}sa {m}dk {s}sn"
        return f"{minutes}dk {seconds}sn"

    # ==================== MONITOR ====================
    def start_monitoring(self, on_status_change: Callable = None):
        """DPI sagligini periyodik kontrol eder"""
        self._monitor_active = True
        self._on_status_change = on_status_change
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        log_info("Izleme baslatildi")

    def stop_monitoring(self):
        self._monitor_active = False
        log_info("Izleme durduruldu")

    def _monitor_loop(self):
        while self._monitor_active:
            time.sleep(MONITOR_INTERVAL)
            if not self._monitor_active:
                break

            running = self.is_running()
            if not running:
                log_info("DPI process durmus, yeniden baslatiliyor...")
                config = self.load_config()
                if config.get("auto_reconnect", True):
                    time.sleep(AUTO_RECONNECT_DELAY)
                    cmd = self.get_working_cmd()
                    if cmd and self.start_dpi_process(cmd):
                        log_info("DPI yeniden baslatildi")
                        if self._on_status_change:
                            self._on_status_change("reconnected", cmd)
                continue

            # Baglanti testi
            any_success = False
            for url in MONITOR_URLS:
                result = test_connection(url, timeout=4)
                if result["success"]:
                    any_success = True
                    break

            if self._on_status_change:
                self._on_status_change(
                    "connected" if any_success else "degraded",
                    None
                )

    # ==================== DNS ====================
    @staticmethod
    def flush_dns() -> bool:
        """DNS onbellegini temizler"""
        try:
            subprocess.run(
                "ipconfig /flushdns",
                shell=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            log_info("DNS temizlendi")
            return True
        except Exception as e:
            log_error(f"DNS temizleme hatasi: {e}")
            return False

    # ==================== PROFIL BILGISI ====================
    def get_profiles(self) -> dict:
        return CMD_PROFILES

    def get_profile_info(self, cmd_file: str) -> dict:
        return CMD_PROFILES.get(cmd_file, {
            "name": cmd_file,
            "desc": "Bilinmeyen profil",
            "priority": 99,
            "category": "diger",
            "tags": []
        })

    def get_sorted_profiles(self) -> list:
        return sorted(
            CMD_PROFILES.items(),
            key=lambda x: x[1]["priority"]
        )

    def get_profiles_by_category(self, category: str) -> list:
        return [
            (k, v) for k, v in CMD_PROFILES.items()
            if v.get("category") == category
        ]

    def get_categories(self) -> list:
        cats = set()
        for p in CMD_PROFILES.values():
            cat = p.get("category", "diger")
            cats.add(cat)
        return sorted(cats)

    # ==================== AUTO TEST ====================
    def auto_test_all(self, progress_cb: Callable = None, status_cb: Callable = None) -> Optional[str]:
        """Tum profilleri otomatik dener, calisani dondurur"""
        sorted_profiles = self.get_sorted_profiles()
        total = len(sorted_profiles)

        for idx, (cmd_file, profile) in enumerate(sorted_profiles):
            if status_cb:
                status_cb(f"Test: {profile['name']} ({idx + 1}/{total})")
            if progress_cb:
                progress_cb(int((idx / total) * 100))

            self.clean_process()
            time.sleep(0.5)

            if not self.start_dpi_process(cmd_file):
                continue

            time.sleep(DPI_WAIT_AFTER_START)

            # Baglanti testi
            success = False
            for url in MONITOR_URLS:
                result = test_connection(url, timeout=4)
                if result["success"]:
                    success = True
                    break

            if success:
                log_info(f"Otomatik test basarili: {cmd_file}")
                if status_cb:
                    status_cb(f"Basarili: {profile['name']}")
                self.set_working_cmd(cmd_file)
                return cmd_file

        # Hicbiri calismadi
        self.clean_process()
        if status_cb:
            status_cb("Hicbir profil calismadi")
        return None

    # ==================== UTILITY ====================
    @staticmethod
    def get_local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Bilinmiyor"
