import { app, BrowserWindow, ipcMain } from "electron";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const createWindow = () => {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    backgroundColor: "#0f111a",
    webPreferences: {
      preload: path.join(__dirname, "preload.js")
    }
  });

  win.loadFile(path.join(__dirname, "renderer", "index.html"));
};

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

ipcMain.handle("goodbyedpi:install", async () => {
  return { status: "Kurulum simülasyonu tamamlandı." };
});

ipcMain.handle("goodbyedpi:start-profile", async (_event, profile) => {
  return { status: `Profil başlatıldı: ${profile}` };
});

ipcMain.handle("goodbyedpi:profile-test", async () => {
  return { status: "Profil testi yakında gerçek verilerle yapılacak." };
});
