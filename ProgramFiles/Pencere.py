# Pencere.py
"""Ana kullanici arayuzu - Yeniden tasarim"""

import sys
import threading
import time
import webbrowser
import platform
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

from config import (
    APP_TITLE, APP_VERSION, WINDOW_SIZE, WINDOW_MIN_SIZE,
    SIDEBAR_WIDTH, COLORS, CMD_PROFILES, MONITOR_URLS
)
from System import DPIService
from utils import (
    log_info, log_error, get_connection_status, test_connection,
    get_log_content, clear_logs, check_for_updates, get_system_info,
    get_public_ip, measure_latency, ensure_dir
)


class ModernDPIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry(WINDOW_SIZE)
        self.minsize(*WINDOW_MIN_SIZE)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.service = DPIService()
        self.current_try_index = 0
        self.sorted_profiles = self.service.get_sorted_profiles()
        self._nav_buttons = []
        self._current_view = None
        self._monitor_active = False
        self._monitor_timer = None

        config = self.service.load_config()
        ctk.set_appearance_mode(config.get("theme", "Dark"))
        ctk.set_default_color_theme("dark-blue")

        self.startup_var = ctk.BooleanVar(value=self.service.check_startup_status())
        self.theme_var = ctk.StringVar(value=config.get("theme", "Dark"))

        if not self.service.is_admin():
            self.service.restart_as_admin()
            return

        ensure_dir(self.service.config_file.rsplit("\\", 1)[0] if "\\" in self.service.config_file else ".")

        self._build_ui()

        self.after(200, self._initialize_app)

    def _build_ui(self):
        """Ana UI yapisini kurar"""
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self._build_sidebar()
        self._build_content()
        self._build_statusbar()

    # ==================== SIDEBAR ====================
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=SIDEBAR_WIDTH, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar, text="🛡️", font=("Arial", 32)
        ).pack(pady=(20, 0))

        ctk.CTkLabel(
            self.sidebar, text="GoodbyeDPI",
            font=("Roboto", 14, "bold")
        ).pack(pady=(2, 0))

        ctk.CTkLabel(
            self.sidebar, text=f"v{APP_VERSION}",
            font=("Roboto", 10), text_color="gray50"
        ).pack(pady=(0, 15))

        nav_items = [
            ("🏠", "Ana Ekran", "dashboard"),
            ("🚀", "Hizli Kurulum", "quick_install"),
            ("⚙️", "Profil Yonetimi", "profiles"),
            ("📊", "Canli Izleme", "monitor"),
            ("🔧", "Ayarlar", "settings"),
            ("📋", "Gunluk", "logs"),
            ("ℹ️", "Hakkinda", "about"),
        ]

        self._nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._nav_frame.pack(fill="x", padx=8, pady=5)

        for icon, text, view in nav_items:
            btn = ctk.CTkButton(
                self._nav_frame,
                text=f"{icon}  {text}",
                font=("Roboto", 12),
                anchor="w",
                height=36,
                fg_color="transparent",
                text_color=("gray20", "gray80"),
                hover_color=("gray70", "gray25"),
                corner_radius=8,
                command=lambda v=view: self._navigate(v)
            )
            btn.pack(fill="x", pady=2)
            self._nav_buttons.append(btn)

    def _highlight_nav(self, active_view: str):
        view_names = ["dashboard", "quick_install", "profiles", "monitor", "settings", "logs", "about"]
        for btn, vname in zip(self._nav_buttons, view_names):
            if vname == active_view:
                btn.configure(fg_color=COLORS["primary"], text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray20", "gray80"))

    # ==================== CONTENT ====================
    def _build_content(self):
        self.content = ctk.CTkFrame(self, corner_radius=15)
        self.content.grid(row=0, column=1, sticky="nsew", padx=(10, 10), pady=(10, 5))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self._content_inner = ctk.CTkFrame(self.content, fg_color="transparent")
        self._content_inner.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self._content_inner.grid_columnconfigure(0, weight=1)
        self._content_inner.grid_rowconfigure(0, weight=1)

    def _build_statusbar(self):
        self.statusbar = ctk.CTkFrame(self, height=28, corner_radius=0)
        self.statusbar.grid(row=1, column=1, sticky="ew", padx=(10, 10), pady=(0, 10))

        self.lbl_status = ctk.CTkLabel(
            self.statusbar, text="Hazir", font=("Roboto", 10),
            text_color="gray50"
        )
        self.lbl_status.pack(side="left", padx=10)

        self.lbl_status_icon = ctk.CTkLabel(
            self.statusbar, text="", font=("Roboto", 10)
        )
        self.lbl_status_icon.pack(side="right", padx=10)

    def set_status(self, text: str, icon: str = ""):
        self.lbl_status.configure(text=text)
        self.lbl_status_icon.configure(text=icon)

    def _clear_content(self):
        for w in self._content_inner.winfo_children():
            w.destroy()

    def _navigate(self, view: str):
        self._highlight_nav(view)
        self._clear_content()

        if view == "dashboard":
            self._show_dashboard()
        elif view == "quick_install":
            self._show_quick_install()
        elif view == "profiles":
            self._show_profiles()
        elif view == "monitor":
            self._show_monitor()
        elif view == "settings":
            self._show_settings()
        elif view == "logs":
            self._show_logs()
        elif view == "about":
            self._show_about()

    # ==================== INIT ====================
    def _initialize_app(self):
        self.set_status("Baslatiliyor...", "⏳")
        cmd = self.service.get_working_cmd()
        if cmd and self.service.is_running():
            self.set_status("Aktif - Profil calisiyor", "🟢")
        elif cmd:
            self.service.clean_process()
            if self.service.start_dpi_process(cmd):
                self.set_status("Aktif", "🟢")
                self.service.start_monitoring(self._on_monitor_event)
            else:
                self.set_status("Profil baslatilamadi", "🔴")
        else:
            self.set_status("Hicbir profil ayarlanmamis", "⚪")
        self._navigate("dashboard")

    # ==================== SCREEN: DASHBOARD ====================
    def _show_dashboard(self):
        frame = self._content_inner

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(header, text="Ana Ekran", font=("Roboto", 22, "bold")).pack(side="left")

        # Durum karti
        cmd = self.service.get_working_cmd()
        running = self.service.is_running()

        status_frame = ctk.CTkFrame(frame, corner_radius=12)
        status_frame.pack(fill="x", pady=(0, 12))

        status_icon = "🟢" if running else "🔴" if cmd else "⚪"
        status_text = "GoodbyeDPI AKTIF" if running else "Durduruldu" if cmd else "Kurulum Yapilmadi"

        ctk.CTkLabel(
            status_frame, text=status_icon, font=("Arial", 36)
        ).pack(pady=(12, 2))

        ctk.CTkLabel(
            status_frame, text=status_text,
            font=("Roboto", 18, "bold"),
            text_color=COLORS["success"] if running else ("gray60")
        ).pack()

        if running and cmd:
            info = self.service.get_profile_info(cmd)
            ctk.CTkLabel(
                status_frame, text=f"Aktif profil: {info['name']}",
                font=("Roboto", 12), text_color="gray50"
            ).pack(pady=(2, 5))

            uptime = self.service.get_uptime()
            if uptime:
                ctk.CTkLabel(
                    status_frame, text=f"Calisma suresi: {uptime}",
                    font=("Roboto", 12), text_color="gray50"
                ).pack(pady=(0, 10))

        if running:
            ctk.CTkButton(
                status_frame, text="⏹ Durdur",
                fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                width=120, command=self._stop_dpi
            ).pack(pady=(5, 12))

        # Hizli aksiyonlar
        actions_frame = ctk.CTkFrame(frame, corner_radius=12)
        actions_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(actions_frame, text="Hizli Aksiyonlar", font=("Roboto", 14, "bold")).pack(pady=(10, 5), padx=15, anchor="w")

        btn_grid = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_grid.pack(pady=(0, 10), padx=15, fill="x")
        btn_grid.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_grid, text="🚀 Hizli Kurulum", height=38,
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=lambda: self._navigate("quick_install")
        ).grid(row=0, column=0, padx=4, pady=3, sticky="ew")

        ctk.CTkButton(
            btn_grid, text="⚙️ Profil Sec", height=38,
            fg_color="transparent", border_width=1, border_color="gray50",
            command=lambda: self._navigate("profiles")
        ).grid(row=0, column=1, padx=4, pady=3, sticky="ew")

        ctk.CTkButton(
            btn_grid, text="📊 Canli Izle", height=38,
            fg_color="transparent", border_width=1, border_color="gray50",
            command=lambda: self._navigate("monitor")
        ).grid(row=1, column=0, padx=4, pady=3, sticky="ew")

        ctk.CTkButton(
            btn_grid, text="🔧 Ayarlar", height=38,
            fg_color="transparent", border_width=1, border_color="gray50",
            command=lambda: self._navigate("settings")
        ).grid(row=1, column=1, padx=4, pady=3, sticky="ew")

        # Baglanti durumu
        conn_frame = ctk.CTkFrame(frame, corner_radius=12)
        conn_frame.pack(fill="x")
        ctk.CTkLabel(conn_frame, text="Baglanti Testi", font=("Roboto", 14, "bold")).pack(pady=(10, 8))

        self._dash_test_frame = ctk.CTkFrame(conn_frame, fg_color="transparent")
        self._dash_test_frame.pack(padx=15, pady=(0, 10), fill="x")

        self._dash_test_label = ctk.CTkLabel(
            self._dash_test_frame, text="Test yapilmadi", font=("Roboto", 11)
        )
        self._dash_test_label.pack()

        ctk.CTkButton(
            conn_frame, text="🔄 Baglantilari Test Et",
            width=160, height=30,
            fg_color="transparent", border_width=1, border_color="gray50",
            command=self._dashboard_connection_test
        ).pack(pady=(0, 10))

    def _dashboard_connection_test(self):
        self._dash_test_label.configure(text="Test ediliyor...")
        threading.Thread(target=self._do_dash_test, daemon=True).start()

    def _do_dash_test(self):
        success, msg, results = get_connection_status()
        details = []
        for url, r in results.items():
            icon = "✅" if r["success"] else "❌"
            lat = f" ({r['latency_ms']}ms)" if r.get("latency_ms") else ""
            details.append(f"{icon} {url.split('//')[1].split('/')[0]}{lat}")

        text = f"{'🟢' if success else '🔴'} {msg}\n" + "\n".join(details)
        self.after(0, lambda: self._dash_test_label.configure(text=text))

    def _stop_dpi(self):
        self.service.clean_process()
        self.service.stop_monitoring()
        self.set_status("Durduruldu", "🔴")
        self.after(100, lambda: self._navigate("dashboard"))

    # ==================== SCREEN: QUICK INSTALL ====================
    def _show_quick_install(self):
        frame = self._content_inner
        self._install_step = 0

        ctk.CTkLabel(
            frame, text="Hizli Kurulum", font=("Roboto", 22, "bold")
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            frame, text="Otomatik kurulum ve test ile dakikalar icinde aktif",
            font=("Roboto", 11), text_color="gray60"
        ).pack(pady=(0, 15))

        self._install_progress_frame = ctk.CTkFrame(frame, corner_radius=12)
        self._install_progress_frame.pack(fill="x", pady=(0, 10))

        self._install_icon = ctk.CTkLabel(
            self._install_progress_frame, text="🛡️", font=("Arial", 48)
        )
        self._install_icon.pack(pady=(15, 5))

        self._install_title = ctk.CTkLabel(
            self._install_progress_frame, text="Hazir",
            font=("Roboto", 16, "bold")
        )
        self._install_title.pack()

        self._install_status = ctk.CTkLabel(
            self._install_progress_frame, text="Hizli Kurulum ile baslayin",
            font=("Roboto", 11), text_color="gray60"
        )
        self._install_status.pack(pady=5)

        self._install_progress = ctk.CTkProgressBar(
            self._install_progress_frame, width=350, height=12
        )
        self._install_progress.pack(pady=10)
        self._install_progress.set(0)

        self._install_percent = ctk.CTkLabel(
            self._install_progress_frame, text="",
            font=("Roboto", 12, "bold"), text_color=COLORS["info"]
        )
        self._install_percent.pack(pady=(0, 15))

        self._install_btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self._install_btn_frame.pack(pady=10)

        self._install_btn = ctk.CTkButton(
            self._install_btn_frame,
            text="🚀 KURULUMU BASLAT",
            height=45, width=220,
            font=("Roboto", 14, "bold"),
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._start_installation
        )
        self._install_btn.pack()

        self._install_options_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self._install_options_frame.pack(fill="x", pady=5)

        self._auto_test_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self._install_options_frame,
            text="Tam otomatik test (onaysiz)",
            variable=self._auto_test_var,
            font=("Roboto", 11)
        ).pack(pady=3)

        self._flush_dns_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self._install_options_frame,
            text="Kurulum sonrasi DNS temizle",
            variable=self._flush_dns_var,
            font=("Roboto", 11)
        ).pack(pady=3)

    def _start_installation(self):
        for w in self._install_btn_frame.winfo_children():
            w.destroy()

        self._install_options_frame.pack_forget()

        self._install_step = 1
        self._install_icon.configure(text="⏳")
        self._install_title.configure(text="Kurulum Basliyor")
        self._install_status.configure(text="Dosyalar hazirlaniyor...")
        self._install_progress.set(0)
        self._install_percent.configure(text="0%")

        threading.Thread(target=self._install_thread, daemon=True).start()

    def _install_thread(self):
        def progress_cb(val):
            self.after(0, lambda: self._update_install_progress(val))

        def status_cb(msg):
            self.after(0, lambda: self._install_status.configure(text=msg))

        success = self.service.download_and_extract(progress_cb, status_cb)

        if success:
            self.after(0, self._start_auto_test)
        else:
            self.after(0, lambda: self._install_failed("Indirme basarisiz!"))

    def _update_install_progress(self, val):
        self._install_progress.set(val / 100)
        self._install_percent.configure(text=f"%{val}")

    def _start_auto_test(self):
        self._install_icon.configure(text="🔍")
        self._install_title.configure(text="Profil Test Ediliyor")
        self._install_progress.set(0)
        self._install_percent.configure(text="")
        self._install_status.configure(text="Test baslatiliyor...")

        if self._auto_test_var.get():
            threading.Thread(target=self._auto_test_all_thread, daemon=True).start()
        else:
            self.after(0, lambda: self._show_manual_test())

    def _auto_test_all_thread(self):
        def status_cb(msg):
            self.after(0, lambda: self._install_status.configure(text=msg))

        def progress_cb(val):
            self.after(0, lambda: self._update_install_progress(val))

        working = self.service.auto_test_all(progress_cb, status_cb)

        if working:
            info = self.service.get_profile_info(working)
            self.after(0, lambda: self._install_success(working, info))
        else:
            self.after(0, lambda: self._install_failed("Hicbir profil calismadi"))

    def _show_manual_test(self):
        """Manuel test icin kullaniciya profil secimini gosterir"""
        self._install_icon.configure(text="⚙️")
        self._install_title.configure(text="Profil Secin")
        self._install_status.configure(text="Size uygun profili secin veya sirasiyla test edin")
        self._install_progress.set(0)
        self._install_percent.configure(text="")

        for w in self._install_btn_frame.winfo_children():
            w.destroy()

        scroll = ctk.CTkScrollableFrame(self._install_btn_frame, width=400, height=180)
        scroll.pack(pady=5)

        for cmd_file, profile in self.sorted_profiles:
            btn = ctk.CTkButton(
                scroll,
                text=f"{profile['name']} - {profile['desc']}",
                font=("Roboto", 11),
                height=38,
                fg_color=("gray75", "gray25"),
                hover_color=COLORS["primary"],
                anchor="w",
                command=lambda c=cmd_file: self._manual_profile_test(c)
            )
            btn.pack(fill="x", pady=2, padx=5)

        ctk.CTkButton(
            self._install_btn_frame, text="← Geri",
            width=100, fg_color="transparent",
            border_width=1, border_color="gray50",
            command=lambda: self._navigate("quick_install")
        ).pack(pady=8)

    def _manual_profile_test(self, cmd_file):
        self._install_icon.configure(text="🔍")
        self._install_title.configure(text="Test Ediliyor...")
        self._install_status.configure(text=f"{cmd_file} test ediliyor")

        for w in self._install_btn_frame.winfo_children():
            w.destroy()

        def do_test():
            self.service.clean_process()
            time.sleep(0.5)
            if not self.service.start_dpi_process(cmd_file):
                self.after(0, lambda: self._install_failed("Profil baslatilamadi!"))
                return
            time.sleep(3)

            success = False
            for url in MONITOR_URLS:
                r = test_connection(url, timeout=4)
                if r["success"]:
                    success = True
                    break

            if success:
                self.service.set_working_cmd(cmd_file)
                info = self.service.get_profile_info(cmd_file)
                self.after(0, lambda: self._install_success(cmd_file, info))
            else:
                self.after(0, lambda: self._manual_test_failed(cmd_file))

        threading.Thread(target=do_test, daemon=True).start()

    def _install_success(self, cmd_file, profile):
        self._install_icon.configure(text="✅")
        self._install_title.configure(text="Kurulum Basarili!", text_color=COLORS["success"])
        self._install_status.configure(text=f"{profile['name']} profili aktif")
        self._install_progress.set(1)
        self._install_percent.configure(text="%100")

        if self._flush_dns_var.get():
            self.service.flush_dns()

        self.set_status(f"Aktif - {profile['name']}", "🟢")

        self._install_options_frame.pack(fill="x", pady=5)

        for w in self._install_btn_frame.winfo_children():
            w.destroy()

        ctk.CTkButton(
            self._install_btn_frame, text="🏠 Ana Ekran",
            width=140, command=lambda: self._navigate("dashboard")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            self._install_btn_frame, text="📊 Canli Izle",
            width=140, fg_color=COLORS["info"],
            command=lambda: self._navigate("monitor")
        ).pack(side="left", padx=5)

    def _install_failed(self, msg):
        self._install_icon.configure(text="❌")
        self._install_title.configure(text="Kurulum Basarisiz", text_color=COLORS["error"])
        self._install_status.configure(text=msg)
        self._install_progress.set(0)
        self._install_percent.configure(text="")

        self._install_options_frame.pack(fill="x", pady=5)

        for w in self._install_btn_frame.winfo_children():
            w.destroy()

        ctk.CTkButton(
            self._install_btn_frame, text="Tekrar Dene",
            width=140, fg_color=COLORS["primary"],
            command=self._start_installation
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            self._install_btn_frame, text="Manuel Sec",
            width=140, fg_color="transparent",
            border_width=1, command=self._show_manual_test
        ).pack(side="left", padx=5)

    def _manual_test_failed(self, cmd_file):
        self._install_status.configure(text=f"{cmd_file} calismadi, baska profil deneyin")
        self._show_manual_test()

    # ==================== SCREEN: PROFILES ====================
    def _show_profiles(self):
        frame = self._content_inner

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Profil Yonetimi", font=("Roboto", 22, "bold")).pack(side="left")

        search_frame = ctk.CTkFrame(frame, corner_radius=8)
        search_frame.pack(fill="x", pady=(0, 10))

        self._profile_search_var = ctk.StringVar()
        self._profile_search_var.trace_add("write", lambda *a: self._filter_profiles())

        ctk.CTkEntry(
            search_frame, textvariable=self._profile_search_var,
            placeholder_text="Profil ara...", height=32
        ).pack(side="left", padx=10, pady=8, fill="x", expand=True)

        self._profile_cat_var = ctk.StringVar(value="Tumu")
        categories = ["Tumu"] + self.service.get_categories()
        ctk.CTkOptionMenu(
            search_frame, values=categories,
            variable=self._profile_cat_var,
            command=lambda _: self._filter_profiles(),
            width=120
        ).pack(side="right", padx=10, pady=8)

        self._profile_scroll = ctk.CTkScrollableFrame(frame, corner_radius=10)
        self._profile_scroll.pack(fill="both", expand=True)

        self._filter_profiles()
        self._update_profile_list()

    def _filter_profiles(self):
        query = self._profile_search_var.get().lower()
        cat = self._profile_cat_var.get()
        self._filtered_profiles = []

        for cmd_file, profile in self.sorted_profiles:
            if cat != "Tumu" and profile.get("category") != cat:
                continue
            if query and query not in cmd_file.lower() and query not in profile["name"].lower():
                continue
            self._filtered_profiles.append((cmd_file, profile))

        self._update_profile_list()

    def _update_profile_list(self):
        for w in self._profile_scroll.winfo_children():
            w.destroy()

        if not self._filtered_profiles:
            ctk.CTkLabel(
                self._profile_scroll, text="Eslesen profil bulunamadi",
                font=("Roboto", 12), text_color="gray50"
            ).pack(pady=30)
            return

        for cmd_file, profile in self._filtered_profiles:
            card = ctk.CTkFrame(self._profile_scroll, corner_radius=10)
            card.pack(fill="x", pady=4, padx=5)

            cat_emoji = {"dns": "🌐", "blacklist": "🚫"}.get(profile.get("category", ""), "⚙️")

            is_fav = self.service.is_favorite(cmd_file)
            fav_icon = "⭐" if is_fav else "☆"
            is_active = self.service.get_working_cmd() == cmd_file and self.service.is_running()
            active_tag = " ✅ AKTIF" if is_active else ""

            ctk.CTkLabel(
                card, text=f"{cat_emoji}  {profile['name']}{active_tag}",
                font=("Roboto", 13, "bold")
            ).pack(pady=(8, 0), padx=12, anchor="w")

            ctk.CTkLabel(
                card, text=profile['desc'],
                font=("Roboto", 10), text_color="gray60"
            ).pack(pady=(0, 5), padx=12, anchor="w")

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(pady=(0, 8), padx=12, fill="x")

            ctk.CTkButton(
                btn_row, text="Baslat",
                width=70, height=28,
                font=("Roboto", 11),
                fg_color=COLORS["success"] if not is_active else COLORS["info"],
                command=lambda c=cmd_file: self._profile_start(c)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_row, text=fav_icon,
                width=35, height=28,
                font=("Roboto", 12),
                fg_color="transparent",
                border_width=1, border_color="gray50",
                command=lambda c=cmd_file: self._profile_toggle_fav(c)
            ).pack(side="left", padx=2)

            ctk.CTkLabel(
                btn_row, text=f"Oncelik: {profile['priority']}",
                font=("Roboto", 10), text_color="gray50"
            ).pack(side="right", padx=5)

    def _profile_start(self, cmd_file):
        self.service.clean_process()
        time.sleep(0.5)
        if self.service.start_dpi_process(cmd_file):
            self.service.set_working_cmd(cmd_file)
            self.set_status(f"Aktif - {self.service.get_profile_info(cmd_file)['name']}", "🟢")
            self._update_profile_list()
        else:
            messagebox.showerror("Hata", "Profil baslatilamadi!")

    def _profile_toggle_fav(self, cmd_file):
        self.service.toggle_favorite(cmd_file)
        self._update_profile_list()

    # ==================== SCREEN: MONITOR ====================
    def _show_monitor(self):
        self._monitor_active = False
        frame = self._content_inner

        ctk.CTkLabel(
            frame, text="Canli Izleme", font=("Roboto", 22, "bold")
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            frame, text="Baglanti durumu ve profil performansi",
            font=("Roboto", 11), text_color="gray60"
        ).pack(pady=(0, 15))

        if not self.service.is_running():
            warn_frame = ctk.CTkFrame(frame, corner_radius=10)
            warn_frame.pack(fill="x", pady=10)

            ctk.CTkLabel(
                warn_frame, text="DPI AKTIF DEGIL",
                font=("Roboto", 16, "bold"), text_color=COLORS["warning"]
            ).pack(pady=(15, 5))

            ctk.CTkLabel(
                warn_frame, text="Izleme yapabilmek icin once bir profili baslatmalisiniz.",
                font=("Roboto", 11), text_color="gray60"
            ).pack(pady=(0, 10))

            btn_frame = ctk.CTkFrame(warn_frame, fg_color="transparent")
            btn_frame.pack(pady=(0, 15))

            cmd = self.service.get_working_cmd()
            if cmd:
                info = self.service.get_profile_info(cmd)
                ctk.CTkButton(
                    btn_frame, text=f"{info['name']} Profilini Baslat",
                    fg_color=COLORS["primary"],
                    command=lambda: self._monitor_start_saved(cmd)
                ).pack()

            ctk.CTkButton(
                btn_frame, text="Profil Sec", fg_color="transparent",
                border_width=1, border_color="gray50",
                command=lambda: self._navigate("profiles")
            ).pack(pady=5)
            return

        self._build_monitor_active(frame)

    def _monitor_start_saved(self, cmd_file):
        if self.service.start_dpi_process(cmd_file):
            self.set_status("Aktif", "🟢")
            self.after(100, lambda: self._navigate("monitor"))

    def _build_monitor_active(self, frame):
        self._monitor_active = True

        info_frame = ctk.CTkFrame(frame, corner_radius=12)
        info_frame.pack(fill="x", pady=(0, 10))

        cmd = self.service.get_working_cmd()
        profile = self.service.get_profile_info(cmd) if cmd else {"name": "Bilinmiyor", "desc": ""}

        ctk.CTkLabel(info_frame, text="🟢", font=("Arial", 32)).pack(pady=(10, 2))
        ctk.CTkLabel(
            info_frame, text=f"Aktif: {profile['name']}",
            font=("Roboto", 16, "bold"), text_color=COLORS["success"]
        ).pack()

        self._monitor_uptime_label = ctk.CTkLabel(
            info_frame, text="", font=("Roboto", 12), text_color="gray50"
        )
        self._monitor_uptime_label.pack()

        ctk.CTkLabel(
            info_frame, text=cmd or "",
            font=("Courier", 9), text_color="gray50"
        ).pack(pady=(0, 10))

        # Test butonlari
        test_frame = ctk.CTkFrame(frame, corner_radius=12)
        test_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(test_frame, text="Baglanti Testi", font=("Roboto", 14, "bold")).pack(pady=(10, 8))

        self._monitor_results_frame = ctk.CTkFrame(test_frame, fg_color="transparent")
        self._monitor_results_frame.pack(padx=15, pady=(0, 5), fill="x")

        self._monitor_results_label = ctk.CTkLabel(
            self._monitor_results_frame, text="Test icin butona tiklayin",
            font=("Roboto", 11), text_color="gray50"
        )
        self._monitor_results_label.pack()

        btn_row = ctk.CTkFrame(test_frame, fg_color="transparent")
        btn_row.pack(pady=(5, 12))

        ctk.CTkButton(
            btn_row, text="🔄 Test Et",
            width=120, fg_color=COLORS["info"],
            command=self._monitor_run_test
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_row, text="🔄 Profil Degistir",
            width=120, fg_color="transparent",
            border_width=1, border_color="gray50",
            command=lambda: self._navigate("profiles")
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_row, text="⏹ Durdur",
            width=100, fg_color=COLORS["danger"],
            command=self._stop_dpi
        ).pack(side="left", padx=4)

        # DNS Flush
        action_frame = ctk.CTkFrame(frame, corner_radius=12)
        action_frame.pack(fill="x")

        ctk.CTkLabel(action_frame, text="Hizli Eylemler", font=("Roboto", 14, "bold")).pack(pady=(10, 8))

        ctk.CTkButton(
            action_frame, text="🧹 DNS Temizle",
            width=140, fg_color="transparent",
            border_width=1, border_color="gray50",
            command=self._monitor_flush_dns
        ).pack(pady=(0, 10))

        self._update_uptime_display()

    def _update_uptime_display(self):
        if not self._monitor_active:
            return
        if hasattr(self, '_monitor_uptime_label'):
            uptime = self.service.get_uptime()
            if uptime:
                self._monitor_uptime_label.configure(text=f"Calisma suresi: {uptime}")
            else:
                self._monitor_uptime_label.configure(text="")
        self.after(1000, self._update_uptime_display)

    def _monitor_run_test(self):
        self._monitor_results_label.configure(text="Test ediliyor...")
        threading.Thread(target=self._monitor_do_test, daemon=True).start()

    def _monitor_do_test(self):
        success, msg, results = get_connection_status()
        lines = [f"{'🟢' if success else '🔴'} {msg}"]
        for url, r in results.items():
            ico = "✅" if r["success"] else "❌"
            lat = f" ({r['latency_ms']}ms)" if r.get("latency_ms") else ""
            status = f"HTTP {r['status_code']}" if r["status_code"] else r.get("error", "hata")
            lines.append(f"  {ico} {url.split('//')[1].split('/')[0]}{lat} - {status}")
        self.after(0, lambda: self._monitor_results_label.configure(text="\n".join(lines)))

    def _monitor_flush_dns(self):
        if self.service.flush_dns():
            messagebox.showinfo("Basarili", "DNS onbellegi temizlendi!")
        else:
            messagebox.showerror("Hata", "DNS temizlenemedi!")

    # ==================== SCREEN: SETTINGS ====================
    def _show_settings(self):
        frame = self._content_inner

        ctk.CTkLabel(frame, text="Ayarlar", font=("Roboto", 22, "bold")).pack(pady=(0, 15))

        scroll = ctk.CTkScrollableFrame(frame, corner_radius=10)
        scroll.pack(fill="both", expand=True)

        # GORUNUM
        self._settings_section(scroll, "Gorunum")
        theme_frame = self._settings_card(scroll, "🎨 Tema")

        theme_menu = ctk.CTkOptionMenu(
            theme_frame, values=["Dark", "Light", "System"],
            variable=self.theme_var,
            command=self.change_theme, width=120
        )
        theme_menu.pack(side="right", padx=15, pady=12)

        # BASLANGIC
        self._settings_section(scroll, "Baslangic")
        startup_card = self._settings_card(scroll, "🚀 Windows ile baslat")

        ctk.CTkLabel(startup_card, text="Bilgisayar acilirken GoodbyeDPI'yi otomatik baslat",
                     font=("Roboto", 11), text_color="gray60").pack(side="left", padx=15, pady=12)

        ctk.CTkSwitch(startup_card, text="", variable=self.startup_var,
                      command=self.toggle_startup).pack(side="right", padx=15, pady=12)

        # OTOMASYON
        self._settings_section(scroll, "Otomasyon")
        config = self.service.load_config()

        def save_setting(key):
            def _(val):
                self.service.save_config(**{key: val})
            return _

        auto_test_frame = self._settings_card(scroll, "🔄 Otomatik test")
        self._auto_test_var_set = ctk.BooleanVar(value=config.get("auto_test", True))
        ctk.CTkLabel(auto_test_frame, text="Test sirasinda otomatik dogrulama",
                     font=("Roboto", 11), text_color="gray60").pack(side="left", padx=15, pady=12)
        ctk.CTkSwitch(auto_test_frame, text="", variable=self._auto_test_var_set,
                      command=lambda: save_setting("auto_test")(self._auto_test_var_set.get())
                      ).pack(side="right", padx=15, pady=12)

        reconnect_frame = self._settings_card(scroll, "🔄 Oto yeniden baglan")
        self._reconnect_var = ctk.BooleanVar(value=config.get("auto_reconnect", True))
        ctk.CTkLabel(reconnect_frame, text="Process durursa otomatik yeniden baslat",
                     font=("Roboto", 11), text_color="gray60").pack(side="left", padx=15, pady=12)
        ctk.CTkSwitch(reconnect_frame, text="", variable=self._reconnect_var,
                      command=lambda: save_setting("auto_reconnect")(self._reconnect_var.get())
                      ).pack(side="right", padx=15, pady=12)

        # AKSIYONLAR
        self._settings_section(scroll, "Aksiyonlar")

        actions_card = ctk.CTkFrame(scroll, corner_radius=10)
        actions_card.pack(fill="x", pady=8, padx=5)

        ctk.CTkButton(
            actions_card, text="🧹 DNS Onbellegini Temizle",
            fg_color="transparent", border_width=1, border_color="gray50",
            command=self._settings_flush_dns
        ).pack(pady=8, padx=15, fill="x")

        ctk.CTkButton(
            actions_card, text="🗑 Ayarlari Sifirla",
            fg_color="transparent", border_width=1,
            border_color=COLORS["error"], text_color=COLORS["error"],
            command=self._reset_config
        ).pack(pady=(0, 8), padx=15, fill="x")

        scroll.pack(fill="both", expand=True)

    def _settings_section(self, parent, title):
        ctk.CTkLabel(
            parent, text=title,
            font=("Roboto", 14, "bold"),
            text_color=COLORS["info"]
        ).pack(pady=(15, 5), padx=5, anchor="w")

    def _settings_card(self, parent, title):
        card = ctk.CTkFrame(parent, corner_radius=8)
        card.pack(fill="x", pady=5, padx=5)

        ctk.CTkLabel(card, text=title, font=("Roboto", 13)).pack(
            side="left", padx=15, pady=12)
        return card

    def change_theme(self, theme):
        ctk.set_appearance_mode(theme)
        self.service.save_config(theme=theme)

    def toggle_startup(self):
        success = self.service.set_startup(self.startup_var.get())
        if not success and getattr(sys, "frozen", False):
            messagebox.showwarning("Uyari", "Baslangic ayari degistirilemedi!")

    def _settings_flush_dns(self):
        DPIService.flush_dns()
        messagebox.showinfo("Basarili", "DNS onbellegi temizlendi!")

    def _reset_config(self):
        if messagebox.askyesno("Onay", "Tum ayarlar sifirlanacak. Emin misiniz?"):
            import os
            try:
                if os.path.exists(self.service.config_file):
                    os.remove(self.service.config_file)
                self.service._config_cache = None
                messagebox.showinfo("Tamam", "Ayarlar sifirlandi. Sayfa yenilenecek.")
                self._navigate("settings")
            except Exception as e:
                messagebox.showerror("Hata", str(e))

    # ==================== SCREEN: LOGS ====================
    def _show_logs(self):
        frame = self._content_inner

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(header, text="Gunluk Kayitlari", font=("Roboto", 22, "bold")).pack(side="left")

        ctk.CTkButton(
            header, text="🔄 Yenile", width=80, height=28,
            font=("Roboto", 11), fg_color="transparent",
            border_width=1, border_color="gray50",
            command=self._refresh_logs
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            header, text="🧹 Temizle", width=80, height=28,
            font=("Roboto", 11), fg_color="transparent",
            border_width=1, border_color=COLORS["error"],
            text_color=COLORS["error"],
            command=self._clear_logs
        ).pack(side="right", padx=4)

        self._log_textbox = ctk.CTkTextbox(frame, font=("Consolas", 11))
        self._log_textbox.pack(fill="both", expand=True)

        self._refresh_logs()

    def _refresh_logs(self):
        content = get_log_content(200)
        self._log_textbox.delete("0.0", "end")
        self._log_textbox.insert("0.0", content)

    def _clear_logs(self):
        if messagebox.askyesno("Onay", "Gunluk kayitlari temizlensin mi?"):
            clear_logs()
            self._refresh_logs()

    # ==================== SCREEN: ABOUT ====================
    def _show_about(self):
        frame = self._content_inner

        scroll = ctk.CTkScrollableFrame(frame, corner_radius=10)
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="🛡️", font=("Arial", 48)).pack(pady=(20, 5))
        ctk.CTkLabel(
            scroll, text=APP_TITLE,
            font=("Roboto", 22, "bold")
        ).pack()
        ctk.CTkLabel(
            scroll, text=f"Surum {APP_VERSION}",
            font=("Roboto", 12), text_color="gray50"
        ).pack()

        ctk.CTkLabel(
            scroll, text="\nGoodbyeDPI Turkiye icin otomatik kurulum ve baslatici.\n"
                        "Tek tikla sansuru asin, ozgur internete kavusun.\n",
            font=("Roboto", 12), justify="center", text_color="gray60"
        ).pack(pady=10)

        # Ozellikler
        features_frame = ctk.CTkFrame(scroll, corner_radius=10)
        features_frame.pack(fill="x", pady=10, padx=20)

        ctk.CTkLabel(features_frame, text="Ozellikler", font=("Roboto", 14, "bold")).pack(pady=(10, 5))
        features = [
            "✅ Otomatik indirme ve kurulum",
            "✅ Akilli profil testi (otomatik/secmeli)",
            "✅ 7 farkli ISP profili",
            "✅ Canli baglanti izleme",
            "✅ Otomatik yeniden baglanma",
            "✅ DNS onbellegi temizleme",
            "✅ Windows baslangicinda calistirma",
            "✅ Karanlik/Aydinlik tema destegi",
            "✅ Detayli hata gunlugu",
        ]
        for f in features:
            ctk.CTkLabel(
                features_frame, text=f, font=("Roboto", 11),
                anchor="w", justify="left"
            ).pack(pady=2, padx=15, anchor="w")
        features_frame.pack(fill="x", pady=10, padx=20)

        # Sistem bilgisi
        sys_frame = ctk.CTkFrame(scroll, corner_radius=10)
        sys_frame.pack(fill="x", pady=10, padx=20)

        ctk.CTkLabel(sys_frame, text="Sistem Bilgisi", font=("Roboto", 14, "bold")).pack(pady=(10, 5))

        sys_info = get_system_info()
        info_items = [
            f"Isletim Sistemi: Windows {sys_info['os_release']}",
            f"Admin yetkisi: {'Evet' if sys_info['is_admin'] else 'Hayir'}",
            f"Python: {sys_info['python_version']}",
            f"Veri yolu: {sys_info['app_data_dir']}",
        ]
        if self.service.is_running():
            cmd = self.service.get_working_cmd()
            if cmd:
                profile = self.service.get_profile_info(cmd)
                info_items.append(f"Aktif profil: {profile['name']}")
                uptime = self.service.get_uptime()
                if uptime:
                    info_items.append(f"Calisma suresi: {uptime}")

        for item in info_items:
            ctk.CTkLabel(
                sys_frame, text=item, font=("Roboto", 11),
                anchor="w", justify="left", text_color="gray60"
            ).pack(pady=2, padx=15, anchor="w")
        sys_frame.pack(fill="x", pady=10, padx=20)

        # IP bilgisi
        ip_frame = ctk.CTkFrame(scroll, corner_radius=10)
        ip_frame.pack(fill="x", pady=10, padx=20)

        ctk.CTkLabel(ip_frame, text="Ag Bilgisi", font=("Roboto", 14, "bold")).pack(pady=(10, 5))

        self._about_ip_label = ctk.CTkLabel(
            ip_frame, text="IP aliniyor...", font=("Roboto", 11), text_color="gray60"
        )
        self._about_ip_label.pack(pady=(0, 10))

        threading.Thread(target=self._about_get_ip, daemon=True).start()

        # Linkler
        links_frame = ctk.CTkFrame(scroll, corner_radius=10)
        links_frame.pack(fill="x", pady=10, padx=20)

        ctk.CTkLabel(links_frame, text="Baglantilar", font=("Roboto", 14, "bold")).pack(pady=(10, 5))

        ctk.CTkButton(
            links_frame, text="📺 YouTube Kanalim",
            fg_color="transparent", border_width=1, border_color="gray50",
            command=lambda: webbrowser.open("https://www.youtube.com/@OzanKE34-m4s")
        ).pack(pady=3, padx=15, fill="x")

        ctk.CTkButton(
            links_frame, text="🐙 GitHub",
            fg_color="transparent", border_width=1, border_color="gray50",
            command=lambda: webbrowser.open("https://github.com/OzanKEreal/GoodbyeDPI-Turkey-Oto-Kurulum")
        ).pack(pady=(3, 10), padx=15, fill="x")

        # Guncelleme kontrol
        update_btn_frame = ctk.CTkFrame(scroll, corner_radius=10)
        update_btn_frame.pack(fill="x", pady=(10, 20), padx=20)

        self._update_check_label = ctk.CTkLabel(
            update_btn_frame, text="", font=("Roboto", 11), text_color="gray60"
        )
        self._update_check_label.pack(pady=5)

        ctk.CTkButton(
            update_btn_frame, text="🔄 Guncelleme Kontrol Et",
            fg_color="transparent", border_width=1, border_color="gray50",
            command=self._about_check_update
        ).pack(pady=(0, 10))

        scroll.pack(fill="both", expand=True)

    def _about_get_ip(self):
        ip = get_public_ip()
        local_ip = self.service.get_local_ip()
        self.after(0, lambda: self._about_ip_label.configure(
            text=f"Yerel IP: {local_ip}  |  Genel IP: {ip}"))

    def _about_check_update(self):
        self._update_check_label.configure(text="Kontrol ediliyor...")
        threading.Thread(target=self._about_do_update_check, daemon=True).start()

    def _about_do_update_check(self):
        result = check_for_updates()
        if result["error"]:
            text = f"Kontrol basarisiz: {result['error']}"
        elif result["has_update"]:
            text = f"Yeni surum var: v{result['latest_version']}! GitHub'dan indirin."
        else:
            text = f"En son surumu kullaniyorsunuz (v{result['latest_version']})"
        self.after(0, lambda: self._update_check_label.configure(text=text))

    # ==================== MONITOR EVENT ====================
    def _on_monitor_event(self, event_type: str, data: str):
        if event_type == "reconnected":
            self.set_status(f"Yeniden baglanildi: {data}", "🟢")
            self.after(2000, lambda: self.set_status("Aktif", "🟢"))
        elif event_type == "degraded":
            self.set_status("Bazi sitelere erisilemiyor", "🟡")
        elif event_type == "connected":
            self.set_status("Aktif", "🟢")

    # ==================== CLOSE ====================
    def on_close(self):
        self._monitor_active = False
        if messagebox.askokcancel("Cikis", "GoodbyeDPI arka planda calismaya devam etsin mi?\n\n"
                                           "Evet = Arka planda calissin\n"
                                           "Hayir = Durdur ve cik"):
            self.service.stop_monitoring()
            log_info("Uygulama kapatildi (arka planda calisiyor)")
            self.destroy()
            sys.exit()
        else:
            self.service.clean_process()
            self.service.stop_monitoring()
            log_info("Uygulama kapatildi (process durduruldu)")
            self.destroy()
            sys.exit()
