import sys
import os
import ctypes
import customtkinter as ctk
from tkinter import messagebox
import requests
import zipfile
import subprocess
import json
import threading
import time
import winreg  # Kayıt defteri işlemleri için (Otomatik başlatma)

# --- AYARLAR ---
GITHUB_URL = "https://github.com/cagritaskn/GoodbyeDPI-Turkey/releases/download/release-0.2.3rc3-turkey/goodbyedpi-0.2.3rc3-turkey.zip"
FOLDER_NAME = "GoodbyeDPI_Files"
CONFIG_FILE = "dpi_config.json"
APP_TITLE = "GoodbyeDPI Turkey - Oto Kurulum"
INSTALL_TIME = 20  # Saniye
APP_NAME_REG = "GoodbyeDPILauncher" # Kayıt defterindeki ad

CMD_FILES = [
    "turkey_dnsredir.cmd",
    "turkey_dnsredir_alternative_superonline.cmd",
    "turkey_dnsredir_alternative2.cmd",
    "turkey_dnsredir_alternative3.cmd",
    "turkey_dnsredir_alternative4_superonline.cmd"
]

# --- UI AYARLARI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class ModernDPIApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Pencere
        self.title(APP_TITLE)
        self.geometry("600x500") # Biraz uzattık
        self.resizable(False, False)
        
        # Değişkenler
        self.process = None
        self.current_try_index = 0
        self.extract_path = os.path.join(os.getcwd(), FOLDER_NAME)
        self.startup_var = ctk.BooleanVar(value=self.check_startup_status())

        # Admin Kontrolü
        if not self.is_admin():
            self.restart_as_admin()
            return

        # Arayüz
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Başlangıç Kontrolü
        if os.path.exists(CONFIG_FILE):
            self.load_saved_config()
        else:
            self.show_welcome_screen()

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def restart_as_admin(self):
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def clean_process(self):
        try:
            subprocess.run("taskkill /F /IM goodbyedpi.exe /T", shell=True, 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

    # --- OTO BAŞLATMA FONKSİYONLARI ---
    def check_startup_status(self):
        """Kayıt defterini kontrol et, program ekli mi?"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, APP_NAME_REG)
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def toggle_startup(self):
        """Checkbox'a tıklandığında çalışır"""
        exe_path = sys.executable
        # Eğer python dosyası olarak çalışıyorsa (geliştirme aşaması) ekleme yapma
        if not getattr(sys, 'frozen', False):
            # print("Geliştirme modunda startup eklenmez.")
            return

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            if self.startup_var.get():
                # Ekle
                winreg.SetValueEx(key, APP_NAME_REG, 0, winreg.REG_SZ, exe_path)
            else:
                # Sil
                try:
                    winreg.DeleteValue(key, APP_NAME_REG)
                except WindowsError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("Hata", f"Başlangıç ayarı değiştirilemedi: {e}")

    # --- EKRAN 1: HOŞGELDİNİZ ---
    def show_welcome_screen(self):
        self.clear_frame()
        lbl_logo = ctk.CTkLabel(self.main_frame, text="🛡️", font=("Arial", 60))
        lbl_logo.pack(pady=(30, 10))
        lbl_title = ctk.CTkLabel(self.main_frame, text="GoodbyeDPI Oto-Kurulum", font=("Roboto", 24, "bold"))
        lbl_title.pack(pady=5)
        lbl_desc = ctk.CTkLabel(self.main_frame, text="YouTube takipçilerim için özel olarak hazırlanmıştır.\nTek tıkla sansürü aşın ve özgür internete kavuşun.", 
                                font=("Roboto", 14), text_color="gray75")
        lbl_desc.pack(pady=10)
        self.btn_start = ctk.CTkButton(self.main_frame, text="KURULUMU BAŞLAT", height=50, width=250, 
                                       font=("Roboto", 16, "bold"), fg_color="#1f538d", hover_color="#14375e",
                                       command=self.start_installation_process)
        self.btn_start.pack(pady=40)

    # --- EKRAN 2: YÜKLEME ---
    def start_installation_process(self):
        self.clear_frame()
        lbl_info = ctk.CTkLabel(self.main_frame, text="Kurulum Hazırlanıyor...", font=("Roboto", 18))
        lbl_info.pack(pady=(50, 10))
        
        # Yorum Kısmı
        yorum = "Arkadaşlar, bu programı sizin için yaptım. Lütfen kanalıma abone olmayı unutmayın! ❤️"
        self.lbl_yorum = ctk.CTkLabel(self.main_frame, text=yorum, font=("Roboto", 14, "italic"), text_color="#f39c12", wraplength=450, justify="center")
        self.lbl_yorum.pack(pady=10)

        self.progress_bar = ctk.CTkProgressBar(self.main_frame, width=400, mode="determinate")
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="%0", text_color="gray")
        self.lbl_status.pack(pady=5)
        threading.Thread(target=self.simulate_installation, daemon=True).start()

    def simulate_installation(self):
        interval = INSTALL_TIME / 100
        for i in range(101):
            time.sleep(interval)
            self.after(0, lambda p=i: self.update_progress(p))
        self.after(0, self.download_and_extract)

    def update_progress(self, val):
        self.progress_bar.set(val / 100)
        self.lbl_status.configure(text=f"%{val} Tamamlandı")

    # --- EKRAN 3: İNDİRME ---
    def download_and_extract(self):
        self.clear_frame()
        lbl_info = ctk.CTkLabel(self.main_frame, text="Dosyalar indiriliyor ve hazırlanıyor...", font=("Roboto", 18))
        lbl_info.pack(pady=(100, 20))
        self.lbl_status = ctk.CTkLabel(self.main_frame, text="İşlem sürüyor...", text_color="gray")
        self.lbl_status.pack(pady=5)
        threading.Thread(target=self.perform_download_and_extract, daemon=True).start()

    def perform_download_and_extract(self):
        try:
            if not os.path.exists(FOLDER_NAME):
                os.makedirs(FOLDER_NAME)
            zip_path = os.path.join(FOLDER_NAME, "temp.zip")
            response = requests.get(GITHUB_URL, stream=True)
            response.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            self.after(0, lambda: self.lbl_status.configure(text="Dosyalar çıkartılıyor..."))
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(FOLDER_NAME)
            os.remove(zip_path)
            time.sleep(1)
            self.after(0, self.start_testing_loop)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Hata", f"İşlem hatası: {e}"))
            self.after(0, self.show_welcome_screen)

    # --- EKRAN 4: TEST ---
    def start_testing_loop(self):
        self.current_try_index = 0
        self.run_test_step()

    def run_test_step(self):
        if self.current_try_index >= len(CMD_FILES):
            self.show_fail_screen()
            return
        cmd_file = CMD_FILES[self.current_try_index]
        self.clean_process()
        self.start_dpi_process(cmd_file)
        self.show_testing_ui(cmd_file)

    def show_testing_ui(self, cmd_file):
        self.clear_frame()
        lbl_anim = ctk.CTkLabel(self.main_frame, text="⚙️", font=("Arial", 50))
        lbl_anim.pack(pady=(30, 10))
        lbl_title = ctk.CTkLabel(self.main_frame, text="Ayar Test Ediliyor", font=("Roboto", 20, "bold"))
        lbl_title.pack(pady=5)
        lbl_file = ctk.CTkLabel(self.main_frame, text=f"Denenen Mod: {self.current_try_index + 1} / {len(CMD_FILES)}\n({cmd_file})", 
                                font=("Roboto", 12), text_color="#3498db")
        lbl_file.pack(pady=5)
        lbl_desc = ctk.CTkLabel(self.main_frame, text="Lütfen tarayıcınızda Roblox veya Discord'u deneyin.\nSiteye erişim sağlandı mı?", font=("Roboto", 14))
        lbl_desc.pack(pady=20)
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        btn_yes = ctk.CTkButton(btn_frame, text="✅ EVET, ÇALIŞTI", fg_color="green", hover_color="darkgreen", 
                                width=150, height=40, command=lambda: self.save_success(cmd_file))
        btn_yes.pack(side="left", padx=10)
        btn_no = ctk.CTkButton(btn_frame, text="❌ HAYIR", fg_color="red", hover_color="darkred", 
                               width=150, height=40, command=self.try_next)
        btn_no.pack(side="left", padx=10)

    def try_next(self):
        self.current_try_index += 1
        self.run_test_step()

    # --- EKRAN 5: BAŞARILI / AKTİF ---
    def save_success(self, cmd_file):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"working_cmd": cmd_file}, f)
        self.show_active_screen(cmd_file)

    def load_saved_config(self):
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            cmd_file = data.get("working_cmd")
        self.clean_process()
        self.start_dpi_process(cmd_file)
        self.show_active_screen(cmd_file)

    def show_active_screen(self, cmd_file):
        self.clear_frame()
        lbl_icon = ctk.CTkLabel(self.main_frame, text="🌐", font=("Arial", 60))
        lbl_icon.pack(pady=(30, 10))
        lbl_status = ctk.CTkLabel(self.main_frame, text="GoodbyeDPI AKTİF", font=("Roboto", 24, "bold"), text_color="#2ecc71")
        lbl_status.pack(pady=5)
        lbl_info = ctk.CTkLabel(self.main_frame, text="Arka planda çalışıyor. Pencereyi kapatırsanız kapanır.", font=("Roboto", 12))
        lbl_info.pack(pady=5)
        lbl_detail = ctk.CTkLabel(self.main_frame, text=f"Aktif Profil: {cmd_file}", font=("Courier", 11), text_color="gray")
        lbl_detail.pack(pady=10)

        # OTO BAŞLAT CHECKBOX
        self.check_startup = ctk.CTkCheckBox(self.main_frame, text="Windows Başlangıcında Otomatik Çalıştır", 
                                             variable=self.startup_var, command=self.toggle_startup,
                                             font=("Roboto", 12))
        self.check_startup.pack(pady=20)

        btn_stop = ctk.CTkButton(self.main_frame, text="DURDUR VE ÇIK", fg_color="#c0392b", hover_color="#922b21", 
                                 width=200, height=50, font=("Roboto", 14, "bold"), command=self.close_app)
        btn_stop.pack(pady=20)

    def show_fail_screen(self):
        self.clear_frame()
        self.clean_process()
        lbl_icon = ctk.CTkLabel(self.main_frame, text="⚠️", font=("Arial", 60))
        lbl_icon.pack(pady=(40, 10))
        lbl_msg = ctk.CTkLabel(self.main_frame, text="Hiçbir Ayar Çalışmadı", font=("Roboto", 20, "bold"), text_color="orange")
        lbl_msg.pack()
        lbl_info = ctk.CTkLabel(self.main_frame, text="Servis sağlayıcınız bu yöntemi engellemiş olabilir.", font=("Roboto", 12))
        lbl_info.pack(pady=20)
        ctk.CTkButton(self.main_frame, text="Kapat", command=self.close_app).pack()

    # --- ARKA PLAN İŞLEMLERİ (SÜPER GİZLİ MOD) ---
    def start_dpi_process(self, cmd_file):
        target_dir = self.extract_path
        for root, dirs, files in os.walk(self.extract_path):
            if cmd_file in files:
                target_dir = root
                break
        
        full_path = os.path.join(target_dir, cmd_file)
        
        if os.path.exists(full_path):
            try:
                # Siyah pencereyi tamamen gizlemek için STARTUPINFO ayarları
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE # Pencereyi gizle

                self.process = subprocess.Popen(
                    [full_path], 
                    cwd=target_dir,
                    # Pencere oluşturma bayrağı
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    # Girdi/Çıktı borularını boşluğa yönlendir (Konsolun görünmesini engeller)
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    startupinfo=si,
                    shell=True
                )
            except Exception as e:
                messagebox.showerror("Hata", str(e))

    def close_app(self):
        self.clean_process()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = ModernDPIApp()
    app.mainloop()