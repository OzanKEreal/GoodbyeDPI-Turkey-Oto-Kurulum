# Tauri + React Geçiş Planı

Bu doküman mevcut GoodbyeDPI-Turkey-Oto-Kurulum projesini **Tauri + React** mimarisine taşımak için
önerilen adımları ve hedef mimariyi özetler.

## 1) Hedef Mimarisi

- **UI (React)**: Kullanıcı arayüzü tamamen web teknolojileriyle (React) geliştirilir.
- **Desktop Shell (Tauri)**: Uygulama kabuğu, Tauri ile sağlanır (Windows/macOS/Linux).
- **Backend (Rust)**: Mevcut Python iş mantığı (download, process, registry) Rust komutlarına taşınır.

## 2) Temel Akış

1. Uygulama başlar.
2. UI üzerinden “Kurulum/İndirme” tetiklenir.
3. Rust komutu GitHub’dan paket indirir ve çıkartır.
4. UI üzerinden “Başlat” denildiğinde Rust komutu ilgili `.cmd` dosyasını çalıştırır.

## 3) Tauri Proje Kurulumu

```bash
# 1) UI projesi (React)
npm create vite@latest ui -- --template react
cd ui
npm install

# 2) Tauri entegrasyonu
npm install -D @tauri-apps/cli
npx tauri init
```

## 4) Backend Komutları (Rust)

Rust tarafında aşağıdaki komutlar oluşturulur:

- `download_and_extract()`
- `start_dpi_process(cmd_file: String)`
- `check_startup_status()`
- `set_startup(enabled: bool)`

Bu komutlar, UI üzerinden `invoke` ile çağrılır.

## 5) Mevcut Python Kodunun Taşınması

Mevcut `ProgramFiles/System.py` işlevleri Rust’a taşınır:

- Download & extract
- CMD dosyasını bulma
- Process yönetimi
- Registry startup (Windows)

## 6) Paketleme ve Dağıtım

```bash
npm run build
npx tauri build
```

Çıktılar:
- Windows: `.exe`
- macOS: `.dmg`
- Linux: `.AppImage`

## 7) Sonraki Adımlar

- UI tasarımı (dark mode, modern layout).
- Profil seçimi ve otomatik test akışının UI’a taşınması.
- Log paneli eklenmesi.

