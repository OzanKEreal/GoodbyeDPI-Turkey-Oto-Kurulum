# config.py
"""Uygulama sabitleri ve ayarları"""

# --- TEMEL AYARLAR ---
APP_TITLE = "GoodbyeDPI Turkey"
APP_VERSION = "1.2.0"
APP_NAME_REG = "GoodbyeDPILauncher"

# --- DOSYA/KLASÖR ---
FOLDER_NAME = "GoodbyeDPI_Files"
CONFIG_FILE = "dpi_config.json"
LOG_FILE = "dpi_app.log"

# --- GITHUB ---
GITHUB_URL = "https://github.com/cagritaskn/GoodbyeDPI-Turkey/releases/download/release-0.2.3rc3-turkey/goodbyedpi-0.2.3rc3-turkey.zip"

# --- CMD PROFİLLERİ ---
CMD_PROFILES = {
    "turkey_dnsredir.cmd": {
        "name": "Standart",
        "desc": "Çoğu ISP için çalışır",
        "priority": 1
    },
    "turkey_dnsredir_alternative_superonline.cmd": {
        "name": "Superonline",
        "desc": "Superonline kullanıcıları için",
        "priority": 2
    },
    "turkey_dnsredir_alternative2.cmd": {
        "name": "Alternatif 2",
        "desc": "Turkcell Superonline alternatif",
        "priority": 3
    },
    "turkey_dnsredir_alternative3.cmd": {
        "name": "Alternatif 3",
        "desc": "Türk Telekom için",
        "priority": 4
    },
    "turkey_dnsredir_alternative4_superonline.cmd": {
        "name": "Alternatif 4",
        "desc": "Son çare profili",
        "priority": 5
    }
}

# --- TEST URL'LERİ ---
TEST_URLS = [
    "https://discord.com",
    "https://www.roblox.com",
    "https://twitter.com"
]

# --- UI AYARLARI ---
WINDOW_SIZE = "620x520"
INSTALL_DURATION = 15  # Saniye

# --- TEMA RENKLERİ ---
COLORS = {
    "success": "#2ecc71",
    "error": "#e74c3c",
    "warning": "#f39c12",
    "info": "#3498db",
    "primary": "#1f538d",
    "primary_hover": "#14375e",
    "danger": "#c0392b",
    "danger_hover": "#922b21"
}