const installBtn = document.getElementById("installBtn");
const profileTestBtn = document.getElementById("profileTestBtn");
const startProfileBtn = document.getElementById("startProfileBtn");
const profileSelect = document.getElementById("profileSelect");
const statusMessage = document.getElementById("statusMessage");
const statusPill = document.getElementById("statusPill");
const progressBar = document.getElementById("progressBar");
const installState = document.getElementById("installState");
const lastRun = document.getElementById("lastRun");
const activeProfile = document.getElementById("activeProfile");

const setBusy = (isBusy) => {
  statusPill.textContent = isBusy ? "İşleniyor" : "Hazır";
  statusPill.classList.toggle("is-busy", isBusy);
  statusPill.classList.toggle("is-ready", !isBusy);
  installBtn.disabled = isBusy;
  profileTestBtn.disabled = isBusy;
  startProfileBtn.disabled = isBusy;
};

const updateProgress = (value) => {
  progressBar.style.width = `${value}%`;
};

installBtn.addEventListener("click", async () => {
  setBusy(true);
  updateProgress(20);
  statusMessage.textContent = "Kurulum başlıyor...";
  const response = await window.goodbyedpi.install();
  installState.textContent = "Yüklendi";
  updateProgress(100);
  statusMessage.textContent = response.status;
  setBusy(false);
});

profileTestBtn.addEventListener("click", async () => {
  setBusy(true);
  updateProgress(40);
  statusMessage.textContent = "Profil testi çalışıyor...";
  const response = await window.goodbyedpi.profileTest();
  updateProgress(100);
  statusMessage.textContent = response.status;
  setBusy(false);
});

startProfileBtn.addEventListener("click", async () => {
  const profile = profileSelect.value;
  if (!profile) {
    statusMessage.textContent = "Lütfen önce bir profil seçin.";
    return;
  }
  setBusy(true);
  updateProgress(60);
  const response = await window.goodbyedpi.startProfile(profile);
  activeProfile.textContent = profile;
  lastRun.textContent = new Date().toLocaleString("tr-TR");
  updateProgress(100);
  statusMessage.textContent = response.status;
  setBusy(false);
});
