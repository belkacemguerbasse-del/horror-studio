function register(ipcMain) {
  ipcMain.handle('comfyui:ping', async (_e, url) => {
    const base = (url || 'http://127.0.0.1:8000').replace(/\/$/, '');
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 2000);
      const r = await fetch(base + '/system_stats', { signal: ctrl.signal });
      clearTimeout(t);
      if (!r.ok) return { ok: false, error: `HTTP ${r.status}` };
      const data = await r.json();
      return { ok: true, data };
    } catch (e) {
      return { ok: false, error: e.message || String(e) };
    }
  });
}

module.exports = { register };
