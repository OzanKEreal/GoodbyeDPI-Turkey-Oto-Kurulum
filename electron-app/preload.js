import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("goodbyedpi", {
  install: () => ipcRenderer.invoke("goodbyedpi:install"),
  startProfile: (profile) =>
    ipcRenderer.invoke("goodbyedpi:start-profile", profile),
  profileTest: () => ipcRenderer.invoke("goodbyedpi:profile-test")
});
