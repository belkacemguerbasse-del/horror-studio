const { app, BrowserWindow, ipcMain, shell, dialog, clipboard, protocol, net } = require('electron');
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');

const isDev = process.env.NODE_ENV === 'development';

protocol.registerSchemesAsPrivileged([
  { scheme: 'local-file', privileges: { standard: true, secure: true, supportFetchAPI: true, stream: true, bypassCSP: true } }
]);

const episodes = require('./ipc/episodes');
const settings = require('./ipc/settings');
const comfyui = require('./ipc/comfyui');
const pipeline = require('./ipc/pipeline');
const elevenlabs = require('./ipc/elevenlabs');

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    backgroundColor: '#0a0a0b',
    title: 'Horror Studio',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }
}

app.whenReady().then(() => {
  protocol.handle('local-file', (req) => {
    try {
      const u = new URL(req.url);
      let p = decodeURIComponent(u.pathname);
      if (process.platform === 'win32' && /^\/[A-Za-z]:/.test(p)) p = p.slice(1);
      if (u.host) p = path.join(u.host + ':\\', p.replace(/^\//, ''));
      return net.fetch(pathToFileURL(p).toString());
    } catch (e) {
      return new Response('Bad path', { status: 400 });
    }
  });

  episodes.register(ipcMain);
  settings.register(ipcMain);
  comfyui.register(ipcMain);
  pipeline.register(ipcMain, () => mainWindow);
  elevenlabs.register(ipcMain);

  ipcMain.handle('app:openPath', (_e, p) => shell.openPath(p));
  ipcMain.handle('app:showItem', (_e, p) => shell.showItemInFolder(p));
  ipcMain.handle('app:pickFiles', async (_e, opts) => {
    const r = await dialog.showOpenDialog(mainWindow, opts || { properties: ['openFile', 'multiSelections'] });
    return r.canceled ? [] : r.filePaths;
  });
  ipcMain.handle('app:pickDir', async () => {
    const r = await dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] });
    return r.canceled ? null : r.filePaths[0];
  });
  ipcMain.handle('app:copyToClipboard', (_e, text) => { clipboard.writeText(text); return true; });
  ipcMain.handle('app:appPath', () => app.getAppPath());
  ipcMain.handle('app:readFileAsDataUrl', (_e, filePath) => {
    if (!filePath || !fs.existsSync(filePath)) return null;
    const ext = path.extname(filePath).toLowerCase().replace('.', '');
    const mime = ext === 'jpg' ? 'image/jpeg' : `image/${ext}`;
    const buf = fs.readFileSync(filePath);
    return `data:${mime};base64,${buf.toString('base64')}`;
  });

  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
