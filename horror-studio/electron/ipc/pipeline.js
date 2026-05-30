const { spawn } = require('child_process');
const path = require('path');
const { store } = require('./settings');

const jobs = new Map();
let nextJobId = 1;

function runPython(script, args, { onLog, onDone, env }) {
  const py = store.get('pythonExe') || 'python';
  const proc = spawn(py, ['-u', script, ...args], {
    cwd: path.dirname(script),
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', ...(env || {}) },
    windowsHide: true
  });

  proc.stdout.on('data', d => onLog && onLog(d.toString()));
  proc.stderr.on('data', d => onLog && onLog(d.toString()));
  proc.on('close', code => onDone && onDone(code));
  proc.on('error', err => {
    onLog && onLog(`\n[SPAWN ERROR] ${err.message}\n`);
    onDone && onDone(1);
  });
  return proc;
}

function register(ipcMain, getWindow) {
  const send = (channel, payload) => {
    const w = getWindow && getWindow();
    if (w && !w.isDestroyed()) w.webContents.send(channel, payload);
  };

  ipcMain.handle('pipeline:generate', (_e, episodeId, opts = {}) => {
    const script = store.get('generateScript');
    const projectsRoot = store.get('projectsRoot');
    const projectDir = path.join(projectsRoot, episodeId);
    const comfyUrl = store.get('comfyUrl');

    const args = [projectDir, '--host', comfyUrl];
    if (opts.only) args.push('--only', String(opts.only));

    const jobId = nextJobId++;
    const log = [];
    const proc = runPython(script, args, {
      onLog: chunk => {
        log.push(chunk);
        send('pipeline:log', { jobId, episodeId, chunk });
        const m = chunk.match(/\[DONE\]\s+(\S+)/);
        if (m) send('pipeline:progress', { jobId, episodeId, frameId: m[1] });
      },
      onDone: code => {
        jobs.delete(jobId);
        send('pipeline:done', { jobId, episodeId, code, kind: 'generate' });
      }
    });
    jobs.set(jobId, proc);
    return { jobId };
  });

  ipcMain.handle('pipeline:concat', (_e, episodeId, opts = {}) => {
    const script = store.get('concatScript');
    const projectsRoot = store.get('projectsRoot');
    const projectDir = path.join(projectsRoot, episodeId);
    const ffmpegPath = (store.get('ffmpegPath') || '').trim();
    const voiceVol   = opts.voiceVolume   ?? store.get('voiceVolume')   ?? 1.10;
    const ambientVol = opts.ambientVolume ?? store.get('ambientVolume') ?? 0.25;
    const noVoice    = !!opts.noVoice;

    const args = [projectDir,
                  '--voice-volume',   String(voiceVol),
                  '--ambient-volume', String(ambientVol)];
    if (noVoice) args.push('--no-voice');

    const jobId = nextJobId++;
    const proc = runPython(script, args, {
      env: ffmpegPath ? { FFMPEG_PATH: ffmpegPath } : {},
      onLog: chunk => send('pipeline:log', { jobId, episodeId, chunk }),
      onDone: code => {
        jobs.delete(jobId);
        send('pipeline:done', { jobId, episodeId, code, kind: 'concat' });
      }
    });
    jobs.set(jobId, proc);
    return { jobId };
  });

  ipcMain.handle('pipeline:cancel', (_e, jobId) => {
    const p = jobs.get(jobId);
    if (p) { try { p.kill('SIGTERM'); } catch {} jobs.delete(jobId); return true; }
    return false;
  });
}

module.exports = { register };
