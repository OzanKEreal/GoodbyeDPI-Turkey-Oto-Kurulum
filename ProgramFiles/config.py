# config.py
"""Uygulama sabitleri ve ayarlari"""

import os

# --- TEMEL AYARLAR ---
APP_TITLE = "GoodbyeDPI Turkey v2"
APP_VERSION = "2.0.0"
APP_NAME_REG = "GoodbyeDPILauncher"
GITHUB_REPO = "OzanKEreal/GoodbyeDPI-Turkey-Oto-Kurulum"

# --- DOSYA/KLASOR YOLLARI ---
APP_DATA_DIR = os.path.join(os.environ.get("APPDATA", os.getcwd()), "GoodbyeDPI-Launcher")
FOLDER_NAME = "GoodbyeDPI_Files"
CONFIG_FILE = os.path.join(APP_DATA_DIR, "dpi_config.json")
LOG_FILE = os.path.join(APP_DATA_DIR, "dpi_app.log")
PID_FILE = os.path.join(APP_DATA_DIR, "process.pid")

# --- GITHUB INDIRME ---
GITHUB_URL = "https://github.com/cagritaskn/GoodbyeDPI-Turkey/releases/download/release-0.2.3rc3-turkey/goodbyedpi-0.2.3rc3-turkey.zip"

# --- GUNCELLEME KONTROL ---
VERSION_CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# --- CMD PROFILLERI ---
CMD_PROFILES = {
    "turkey_dnsredir.cmd": {
        "name": "Standart (Onerilen)",
        "desc": "Cogu ISP icin calisir - DNS yonlendirme",
        "priority": 1,
        "category": "dns",
        "tags": ["standart", "dns", "genel"]
    },
    "turkey_dnsredir_alternative_superonline.cmd": {
        "name": "Superonline",
        "desc": "Superonline kullanicilari icin ozel cozum",
        "priority": 2,
        "category": "dns",
        "tags": ["superonline", "dns"]
    },
    "turkey_dnsredir_alternative2.cmd": {
        "name": "Alternatif 2",
        "desc": "Turkcell ve Superonline icin alternatif",
        "priority": 3,
        "category": "dns",
        "tags": ["turkcell", "superonline", "alternatif"]
    },
    "turkey_dnsredir_alternative3.cmd": {
        "name": "Turk Telekom",
        "desc": "Turk Telekom kullanicilari icin",
        "priority": 4,
        "category": "dns",
        "tags": ["turktelekom", "ttnet"]
    },
    "turkey_dnsredir_alternative4_superonline.cmd": {
        "name": "Alternatif 4 (Son Care)",
        "desc": "Diger profiller calismazsa deneyin",
        "priority": 5,
        "category": "dns",
        "tags": ["soncare", "alternatif"]
    },
    "turkey_blacklist_dnsredir.cmd": {
        "name": "Kara Liste DNS",
        "desc": "Kara liste tabanli DNS yonlendirme",
        "priority": 6,
        "category": "blacklist",
        "tags": ["karaliste", "dns"]
    },
    "turkey_blacklist_dnsredir_alternative.cmd": {
        "name": "Kara Liste Alt",
        "desc": "Kara liste alternatif profil",
        "priority": 7,
        "category": "blacklist",
        "tags": ["karaliste", "alternatif"]
    }
}

# --- TEST URL'LERI ---
TEST_URLS = [
    "https://discord.com",
    "https://www.roblox.com",
    "https://twitter.com",
    "https://www.instagram.com",
    "https://www.youtube.com",
    "https://www.google.com"
]

MONITOR_URLS = [
    "https://discord.com",
    "https://www.roblox.com",
    "https://twitter.com"
]

# --- UI AYARLARI ---
WINDOW_SIZE = "820x620"
WINDOW_MIN_SIZE = (700, 500)
SIDEBAR_WIDTH = 180

# --- ZAMAN ASIMLARI ---
DPI_WAIT_AFTER_START = 3  # DPI basladiktan sonra bekleme saniye
MONITOR_INTERVAL = 30     # Izleme araligi saniye
AUTO_RECONNECT_DELAY = 5  # Yeniden baglanma gecikmesi saniye

# --- TEMA RENKLERI ---
COLORS = {
    "success": "#2ecc71",
    "error": "#e74c3c",
    "warning": "#f39c12",
    "info": "#3498db",
    "primary": "#1f538d",
    "primary_hover": "#14375e",
    "danger": "#c0392b",
    "danger_hover": "#922b21",
    "bg_dark": "#1a1a2e",
    "card_dark": "#16213e",
    "bg_light": "#f0f0f0",
    "card_light": "#ffffff"
}
