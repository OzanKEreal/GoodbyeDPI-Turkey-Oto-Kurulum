# Pencere.py
"""Ana kullanıcı arayüzü"""

import sys
import threading
import time
import customtkinter as ctk
from tkinter import messagebox

from config import (
    APP_TITLE, APP_VERSION, WINDOW_SIZE, 
    INSTALL_DURATION, COLORS, CMD_PROFILES
)
from System import DPIService
from utils import log_info, log_error, get_connection_status, test_connection


class ModernDPIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Pencere Ayarları
        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry(WINDOW_SIZE)
        self.resizable(False, False)

        # Service
        self.service = DPIService()
        self.current_try_index = 0
        self.sorted_profiles = self.service.get_sorted_profiles()

        # Tema
        config = self.service.load_config()
        ctk.set_appearance_mode(config.get("theme", "Dark"))
        ctk.set_default_color_theme("dark-blue")

        # Değişkenler
        self.startup_var = ctk.BooleanVar(value=self.service.check_startup_status())
        self.theme_var = ctk.StringVar(value=config.get("theme", "Dark"))

        # Admin Kontrol
        if not self.service.is_admin():
            self.service.restart_as_admin()
            return

        # Ana Frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Başlangıç
        self._initialize_app()

    def _initialize_app(self):
        """Uygulama başlangıç kontrolü"""
        cmd = self.service.get_working_cmd()
        if cmd:
            self.service.clean_process()
            if self.service.start_dpi_process(cmd):
                self.show_active_screen(cmd)
            else:
                self.show_welcome_screen()
        else:
            self.show_welcome_screen()

    def clear_frame(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

    # ==================== EKRAN 1: HOŞGELDİN ====================
    def show_welcome_screen(self):
        self.clear_frame()
        
        # Logo
        ctk.CTkLabel(self.main_frame, text="🛡️", font=("Arial", 60)).pack(pady=(30, 5))
        
        # Başlık
        ctk.CTkLabel(
            self.main_frame, 
            text=f"{APP_TITLE}", 
            font=("Roboto", 24, "bold")
        ).pack(pady=5)
        
        # Alt başlık
        ctk.CTkLabel(
            self.main_frame,
            text=f"v{APP_VERSION} • YouTube için özel olarak hazırlandı",
            font=("Roboto", 12),
            text_color="gray60"
        ).pack(pady=5)
        
        # Açıklama
        ctk.CTkLabel(
            self.main_frame,
            text="Tek tıkla sansürü aşın ve özgür internete kavuşun.\nDiscord, Roblox ve daha fazlasına erişin.",
            font=("Roboto", 14),
            text_color="gray75",
            justify="center"
        ).pack(pady=15)

        # Butonlar
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=30)

        # Otomatik Kurulum
        ctk.CTkButton(
            btn_frame,
            text="🚀 OTOMATİK KURULUM",
            height=50,
            width=220,
            font=("Roboto", 15, "bold"),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self.start_installation
        ).pack(pady=5)

        # Manuel Seçim
        ctk.CTkButton(
            btn_frame,
            text="⚙️ Manuel Profil Seç",
            height=40,
            width=220,
            font=("Roboto", 13),
            fg_color="transparent",
            border_width=2,
            border_color=COLORS["info"],
            hover_color=("gray70", "gray30"),
            command=self.show_manual_selection
        ).pack(pady=5)

        # Ayarlar (Alt köşe)
        ctk.CTkButton(
            self.main_frame,
            text="⚙",
            width=35,
            height=35,
            corner_radius=20,
            fg_color="gray30",
            hover_color="gray40",
            command=self.show_settings
        ).place(relx=0.95, rely=0.95, anchor="se")

    # ==================== EKRAN 2: KURULUM PROGRESS ====================
    def start_installation(self):
        self.clear_frame()

        ctk.CTkLabel(
            self.main_frame, 
            text="⏳", 
            font=("Arial", 50)
        ).pack(pady=(40, 10))

        ctk.CTkLabel(
            self.main_frame,
            text="Kurulum Başlıyor...",
            font=("Roboto", 20, "bold")
        ).pack(pady=5)

        self.lbl_install_status = ctk.CTkLabel(
            self.main_frame,
            text="Dosyalar hazırlanıyor...",
            font=("Roboto", 12),
            text_color="gray60"
        )
        self.lbl_install_status.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=400, height=15)
        self.progress_bar.pack(pady=15)
        self.progress_bar.set(0)

        self.lbl_percent = ctk.CTkLabel(
            self.main_frame,
            text="0%",
            font=("Roboto", 14, "bold"),
            text_color=COLORS["info"]
        )
        self.lbl_percent.pack(pady=5)

        # İndirme thread
        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        def progress_cb(val):
            self.after(0, lambda: self._update_progress(val))

        def status_cb(msg):
            self.after(0, lambda: self.lbl_install_status.configure(text=msg))

        success = self.service.download_and_extract(progress_cb, status_cb)

        if success:
            self.after(500, self.start_testing_loop)
        else:
            self.after(0, lambda: messagebox.showerror("Hata", "İndirme başarısız!"))
            self.after(0, self.show_welcome_screen)

    def _update_progress(self, val):
        self.progress_bar.set(val / 100)
        self.lbl_percent.configure(text=f"{val}%")

    # ==================== EKRAN 3: TEST ====================
    def start_testing_loop(self):
        self.current_try_index = 0
        self.run_test_step()

    def run_test_step(self):
        if self.current_try_index >= len(self.sorted_profiles):
            self.show_fail_screen()
            return

        cmd_file, profile = self.sorted_profiles[self.current_try_index]
        self.service.clean_process()

        if self.service.start_dpi_process(cmd_file):
            self.show_testing_ui(cmd_file, profile)
        else:
            self.current_try_index += 1
            self.run_test_step()

    def show_testing_ui(self, cmd_file, profile):
        self.clear_frame()

        ctk.CTkLabel(self.main_frame, text="🔍", font=("Arial", 50)).pack(pady=(30, 10))
        ctk.CTkLabel(
            self.main_frame,
            text="Ayar Test Ediliyor",
            font=("Roboto", 20, "bold")
        ).pack(pady=5)

        # Profil bilgisi
        info_frame = ctk.CTkFrame(self.main_frame, fg_color=("gray85", "gray20"), corner_radius=10)
        info_frame.pack(pady=15, padx=40, fill="x")

        ctk.CTkLabel(
            info_frame,
            text=f"📌 {profile['name']}",
            font=("Roboto", 14, "bold")
        ).pack(pady=(10, 2))
        
        ctk.CTkLabel(
            info_frame,
            text=profile['desc'],
            font=("Roboto", 11),
            text_color="gray60"
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            info_frame,
            text=f"Deneme: {self.current_try_index + 1} / {len(self.sorted_profiles)}",
            font=("Roboto", 11),
            text_color=COLORS["info"]
        ).pack(pady=(0, 10))

        # Talimat
        ctk.CTkLabel(
            self.main_frame,
            text="Tarayıcınızda Discord veya Roblox'u deneyin.\nSiteye erişebildiniz mi?",
            font=("Roboto", 13),
            justify="center"
        ).pack(pady=15)

        # Butonlar
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="✅ EVET, ÇALIŞTI",
            fg_color=COLORS["success"],
            hover_color="#27ae60",
            width=140,
            height=45,
            font=("Roboto", 13, "bold"),
            command=lambda: self.save_success(cmd_file)
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame,
            text="❌ HAYIR",
            fg_color=COLORS["error"],
            hover_color="#c0392b",
            width=140,
            height=45,
            font=("Roboto", 13, "bold"),
            command=self.try_next
        ).pack(side="left", padx=8)

        # Otomatik test butonu
        ctk.CTkButton(
            self.main_frame,
            text="🔄 Otomatik Test Et",
            width=180,
            height=35,
            fg_color="transparent",
            border_width=1,
            border_color="gray50",
            hover_color=("gray70", "gray30"),
            command=lambda: self.auto_test(cmd_file)
        ).pack(pady=10)

    def auto_test(self, cmd_file):
        """Otomatik bağlantı testi"""
        self.clear_frame()
        ctk.CTkLabel(self.main_frame, text="🔄", font=("Arial", 50)).pack(pady=(60, 15))
        lbl = ctk.CTkLabel(self.main_frame, text="Bağlantı test ediliyor...", font=("Roboto", 16))
        lbl.pack()

        def test_thread():
            time.sleep(2)  # DPI'ın devreye girmesi için bekle
            success, msg = get_connection_status()
            
            if success:
                self.after(0, lambda: self.save_success(cmd_file))
            else:
                self.after(0, self.try_next)

        threading.Thread(target=test_thread, daemon=True).start()

    def try_next(self):
        self.current_try_index += 1
        self.run_test_step()

    # ==================== EKRAN 4: MANUEL SEÇİM ====================
    def show_manual_selection(self):
        self.clear_frame()

        ctk.CTkLabel(self.main_frame, text="⚙️", font=("Arial", 45)).pack(pady=(20, 10))
        ctk.CTkLabel(
            self.main_frame,
            text="Manuel Profil Seçimi",
            font=("Roboto", 20, "bold")
        ).pack(pady=5)
        ctk.CTkLabel(
            self.main_frame,
            text="İnternet sağlayıcınıza uygun profili seçin",
            font=("Roboto", 12),
            text_color="gray60"
        ).pack(pady=5)

        # Profil listesi
        scroll_frame = ctk.CTkScrollableFrame(self.main_frame, width=450, height=250)
        scroll_frame.pack(pady=15, padx=20)

        for cmd_file, profile in self.sorted_profiles:
            btn = ctk.CTkButton(
                scroll_frame,
                text=f"📌 {profile['name']}\n{profile['desc']}",
                font=("Roboto", 12),
                height=55,
                fg_color=("gray75", "gray25"),
                hover_color=COLORS["primary"],
                anchor="w",
                command=lambda c=cmd_file: self.manual_start(c)
            )
            btn.pack(fill="x", pady=4, padx=5)

        # Geri butonu
        ctk.CTkButton(
            self.main_frame,
            text="← Geri",
            width=100,
            fg_color="transparent",
            border_width=1,
            border_color="gray50",
            command=self.show_welcome_screen
        ).pack(pady=10)

    def manual_start(self, cmd_file):
        """Manuel seçilen profili başlat"""
        # Önce dosyaların indirilip indirilmediğini kontrol et
        if not self.service._find_cmd_path(cmd_file):
            if messagebox.askyesno("Dosyalar Eksik", "Dosyalar henüz indirilmemiş. İndirmek ister misiniz?"):
                self.start_installation()
            return

        self.service.clean_process()
        if self.service.start_dpi_process(cmd_file):
            self.save_success(cmd_file)
        else:
            messagebox.showerror("Hata", "Profil başlatılamadı!")

    # ==================== EKRAN 5: AKTİF ====================
    def save_success(self, cmd_file):
        self.service.set_working_cmd(cmd_file)
        log_info(f"Çalışan profil kaydedildi: {cmd_file}")
        self.show_active_screen(cmd_file)

    def show_active_screen(self, cmd_file):
        self.clear_frame()
        profile = self.service.get_profile_info(cmd_file)

        ctk.CTkLabel(self.main_frame, text="🌐", font=("Arial", 55)).pack(pady=(25, 10))
        
        ctk.CTkLabel(
            self.main_frame,
            text="GoodbyeDPI AKTİF",
            font=("Roboto", 24, "bold"),
            text_color=COLORS["success"]
        ).pack(pady=5)

        ctk.CTkLabel(
            self.main_frame,
            text="Arka planda çalışıyor • Pencereyi kapatırsanız durur",
            font=("Roboto", 11),
            text_color="gray60"
        ).pack(pady=5)

        # Profil kartı
        card = ctk.CTkFrame(self.main_frame, fg_color=("gray85", "gray20"), corner_radius=10)
        card.pack(pady=15, padx=50, fill="x")

        ctk.CTkLabel(card, text=f"📌 Aktif: {profile['name']}", font=("Roboto", 13, "bold")).pack(pady=(10, 2))
        ctk.CTkLabel(card, text=cmd_file, font=("Courier", 10), text_color="gray50").pack(pady=(0, 10))

        # Ayarlar
        settings_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        settings_frame.pack(pady=10)

        ctk.CTkCheckBox(
            settings_frame,
            text="Windows başlangıcında çalıştır",
            variable=self.startup_var,
            command=self.toggle_startup,
            font=("Roboto", 12)
        ).pack(pady=5)

        # Butonlar
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="🔄 Profil Değiştir",
            width=130,
            height=40,
            fg_color=COLORS["info"],
            hover_color="#2980b9",
            command=self.show_manual_selection
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame,
            text="⏹ Durdur ve Çık",
            width=130,
            height=40,
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            command=self.close_app
        ).pack(side="left", padx=8)

    # ==================== EKRAN 6: BAŞARISIZ ====================
    def show_fail_screen(self):
        self.clear_frame()
        self.service.clean_process()

        ctk.CTkLabel(self.main_frame, text="⚠️", font=("Arial", 55)).pack(pady=(40, 10))
        ctk.CTkLabel(
            self.main_frame,
            text="Hiçbir Profil Çalışmadı",
            font=("Roboto", 20, "bold"),
            text_color=COLORS["warning"]
        ).pack(pady=5)
        ctk.CTkLabel(
            self.main_frame,
            text="İnternet sağlayıcınız bu yöntemi engelliyor olabilir.\nManuel profil seçmeyi deneyin veya daha sonra tekrar deneyin.",
            font=("Roboto", 12),
            text_color="gray60",
            justify="center"
        ).pack(pady=15)

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Manuel Seç",
            width=120,
            command=self.show_manual_selection
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Kapat",
            width=120,
            fg_color="gray40",
            command=self.close_app
        ).pack(side="left", padx=10)

    # ==================== EKRAN 7: AYARLAR ====================
    def show_settings(self):
        self.clear_frame()

        ctk.CTkLabel(self.main_frame, text="⚙️", font=("Arial", 45)).pack(pady=(25, 10))
        ctk.CTkLabel(self.main_frame, text="Ayarlar", font=("Roboto", 20, "bold")).pack(pady=5)

        settings_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        settings_frame.pack(pady=20, padx=40, fill="x")

        # Tema
        theme_frame = ctk.CTkFrame(settings_frame, fg_color=("gray85", "gray20"), corner_radius=8)
        theme_frame.pack(fill="x", pady=8)
        
        ctk.CTkLabel(theme_frame, text="🎨 Tema", font=("Roboto", 13)).pack(side="left", padx=15, pady=12)
        
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Dark", "Light", "System"],
            variable=self.theme_var,
            command=self.change_theme,
            width=120
        )
        theme_menu.pack(side="right", padx=15, pady=12)

        # Startup
        startup_frame = ctk.CTkFrame(settings_frame, fg_color=("gray85", "gray20"), corner_radius=8)
        startup_frame.pack(fill="x", pady=8)
        
        ctk.CTkLabel(startup_frame, text="🚀 Windows ile başlat", font=("Roboto", 13)).pack(side="left", padx=15, pady=12)
        
        ctk.CTkSwitch(
            startup_frame,
            text="",
            variable=self.startup_var,
            command=self.toggle_startup
        ).pack(side="right", padx=15, pady=12)

        # Config sıfırla
        ctk.CTkButton(
            settings_frame,
            text="🗑 Ayarları Sıfırla",
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["error"],
            text_color=COLORS["error"],
            hover_color=("gray80", "gray25"),
            command=self.reset_config
        ).pack(pady=20)

        # Geri
        ctk.CTkButton(
            self.main_frame,
            text="← Geri",
            width=100,
            fg_color="transparent",
            border_width=1,
            border_color="gray50",
            command=self.show_welcome_screen
        ).pack(pady=10)

    def change_theme(self, theme):
        ctk.set_appearance_mode(theme)
        self.service.save_config(theme=theme)

    def toggle_startup(self):
        success = self.service.set_startup(self.startup_var.get())
        if not success and getattr(sys, "frozen", False):
            messagebox.showwarning("Uyarı", "Başlangıç ayarı değiştirilemedi!")

    def reset_config(self):
        if messagebox.askyesno("Onay", "Tüm ayarlar sıfırlanacak. Emin misiniz?"):
            import os
            try:
                os.remove(self.service.config_file)
                self.service._config_cache = None
                messagebox.showinfo("Tamam", "Ayarlar sıfırlandı. Uygulama yeniden başlatılacak.")
                self.close_app()
            except Exception as e:
                messagebox.showerror("Hata", str(e))

    def close_app(self):
        self.service.clean_process()
        log_info("Uygulama kapatıldı")
        self.destroy()
        sys.exit()