# System.py
"""Çekirdek iş mantığı - Download, Process, Registry işlemleri"""

import os
import sys
import ctypes
import json
import zipfile
import subprocess
import requests
import winreg
from typing import Callable, Optional

from config import (
    GITHUB_URL, FOLDER_NAME, CONFIG_FILE, 
    APP_NAME_REG, CMD_PROFILES, COLORS
)
from utils import log_info, log_error, log_debug, ensure_dir


class DPIService:
    """GoodbyeDPI servis yöneticisi"""
    
    def __init__(self):
        self.github_url = GITHUB_URL
        self.folder_name = FOLDER_NAME
        self.config_file = CONFIG_FILE
        self.extract_path = os.path.join(os.getcwd(), self.folder_name)
        self.process = None
        self._config_cache = None
        
        log_info("DPIService başlatıldı")

    # ==================== ADMIN ====================
    @staticmethod
    def is_admin() -> bool:
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    @staticmethod
    def restart_as_admin():
        log_info("Admin olarak yeniden başlatılıyor...")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

    # ==================== CONFIG ====================
    def load_config(self) -> dict:
        """Config dosyasını yükler"""
        if self._config_cache:
            return self._config_cache
            
        default = {
            "working_cmd": None,
            "theme": "Dark",
            "auto_start": False,
            "auto_test": True,
            "last_run": None
        }
        
        if not os.path.exists(self.config_file):
            return default
            
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Eksik anahtarları default ile doldur
                for key, val in default.items():
                    if key not in data:
                        data[key] = val
                self._config_cache = data
                return data
        except Exception as e:
            log_error(f"Config okuma hatası: {e}")
            return default

    def save_config(self, **kwargs):
        """Config dosyasını günceller"""
        config = self.load_config()
        config.update(kwargs)
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self._config_cache = config
            log_info(f"Config kaydedildi: {kwargs}")
        except Exception as e:
            log_error(f"Config kaydetme hatası: {e}")

    def get_working_cmd(self) -> Optional[str]:
        return self.load_config().get("working_cmd")

    def set_working_cmd(self, cmd_file: str):
        self.save_config(working_cmd=cmd_file)

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
        """Başlangıç ayarını değiştirir. Başarılı ise True döner."""
        if not getattr(sys, "frozen", False):
            log_debug("Dev modda startup atlandı")
            return False

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_ALL_ACCESS
            )
            
            if enabled:
                winreg.SetValueEx(key, APP_NAME_REG, 0, winreg.REG_SZ, sys.executable)
                log_info("Startup eklendi")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME_REG)
                    log_info("Startup kaldırıldı")
                except OSError:
                    pass
                    
            winreg.CloseKey(key)
            self.save_config(auto_start=enabled)
            return True
            
        except Exception as e:
            log_error(f"Startup ayarlama hatası: {e}")
            return False

    # ==================== DOWNLOAD & EXTRACT ====================
    def download_and_extract(
        self, 
        progress_cb: Callable[[int], None] = None,
        status_cb: Callable[[str], None] = None
    ) -> bool:
        """
        Dosyaları indirir ve çıkarır.
        progress_cb: 0-100 arası ilerleme
        status_cb: Durum mesajı
        """
        try:
            ensure_dir(self.folder_name)
            zip_path = os.path.join(self.folder_name, "temp.zip")

            # İndirme
            if status_cb:
                status_cb("Bağlantı kuruluyor...")
            
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
                            pct = int((downloaded / total_size) * 50)  # 0-50%
                            progress_cb(pct)

            # Çıkartma
            if status_cb:
                status_cb("Dosyalar çıkartılıyor...")
            
            with zipfile.ZipFile(zip_path, "r") as z:
                files = z.namelist()
                for i, file in enumerate(files):
                    z.extract(file, self.folder_name)
                    if progress_cb:
                        pct = 50 + int((i / len(files)) * 50)  # 50-100%
                        progress_cb(pct)

            os.remove(zip_path)
            
            if progress_cb:
                progress_cb(100)
            if status_cb:
                status_cb("Tamamlandı!")
                
            log_info("Download ve extract başarılı")
            return True

        except Exception as e:
            log_error(f"Download/extract hatası: {e}")
            if status_cb:
                status_cb(f"Hata: {e}")
            return False

    # ==================== PROCESS MANAGEMENT ====================
    def clean_process(self):
        """Çalışan GoodbyeDPI process'lerini temizler"""
        try:
            subprocess.run(
                "taskkill /F /IM goodbyedpi.exe /T",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.process = None
            log_debug("Process temizlendi")
        except Exception as e:
            log_error(f"Process temizleme hatası: {e}")

    def _find_cmd_path(self, cmd_file: str) -> Optional[str]:
        """CMD dosyasının tam yolunu bulur"""
        for root, _, files in os.walk(self.extract_path):
            if cmd_file in files:
                return os.path.join(root, cmd_file)
        return None

    def start_dpi_process(self, cmd_file: str) -> bool:
        """DPI process'i başlatır. Başarılı ise True döner."""
        full_path = self._find_cmd_path(cmd_file)
        
        if not full_path:
            log_error(f"CMD bulunamadı: {cmd_file}")
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
            
            log_info(f"DPI başlatıldı: {cmd_file}")
            return True

        except Exception as e:
            log_error(f"DPI başlatma hatası: {e}")
            return False

    def is_running(self) -> bool:
        """Process çalışıyor mu kontrol eder"""
        if self.process is None:
            return False
        return self.process.poll() is None

    # ==================== PROFIL BİLGİSİ ====================
    def get_profiles(self) -> dict:
        """Mevcut profilleri döndürür"""
        return CMD_PROFILES

    def get_profile_info(self, cmd_file: str) -> dict:
        """Belirli profilin bilgisini döndürür"""
        return CMD_PROFILES.get(cmd_file, {
            "name": cmd_file,
            "desc": "Bilinmeyen profil",
            "priority": 99
        })

    def get_sorted_profiles(self) -> list:
        """Priority'ye göre sıralı profil listesi"""
        return sorted(
            CMD_PROFILES.items(),
            key=lambda x: x[1]["priority"]
        )