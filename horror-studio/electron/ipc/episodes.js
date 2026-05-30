const fs = require('fs');
const path = require('path');
const { store } = require('./settings');

const FRAME_COUNT = 10;

function projectsRoot() { return store.get('projectsRoot'); }
function slugify(s) {
  return String(s || 'untitled')
    .toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 40) || 'episode';
}

function ensureRoot() {
  const root = projectsRoot();
  if (!fs.existsSync(root)) fs.mkdirSync(root, { recursive: true });
  return root;
}

function readJSON(file, fallback = null) {
  try { return JSON.parse(fs.readFileSync(file, 'utf-8')); }
  catch { return fallback; }
}
function writeJSON(file, data) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf-8');
}

function metaPath(id)    { return path.join(projectsRoot(), id, 'meta.json'); }
function promptsPath(id) { return path.join(projectsRoot(), id, 'prompts.json'); }
function framesDir(id)   { return path.join(projectsRoot(), id, 'frames'); }
function outputDir(id)   { return path.join(projectsRoot(), id, 'output'); }
function voicePath(id)   { return path.join(projectsRoot(), id, 'voiceover.md'); }

function defaultMeta(id, title, scheduledFor) {
  return {
    id,
    title: title || 'Untitled',
    storyIntent: '',
    bananaPromptCopied: false,
    scheduledFor: scheduledFor || new Date().toISOString().slice(0, 10),
    status: 'draft', // draft | storyboard | prompts | generating | ready | posted
    posted: false,
    postedAt: null,
    tiktokUrl: '',
    notes: '',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
}

function defaultPrompts() {
  const s = store.store;
  return {
    story_title: 'Untitled',
    global_negative: 'characters speaking foreign language, gibberish dialogue, mouthing words',
    width: s.defaultWidth,
    height: s.defaultHeight,
    fps: s.defaultFps,
    frames: Array.from({ length: FRAME_COUNT }, (_, i) => ({
      id: String(i + 1).padStart(2, '0'),
      image: `frames/${String(i + 1).padStart(2, '0')}.png`,
      duration: s.defaultDuration,
      prompt: ''
    }))
  };
}

function computeStatus(id) {
  const meta = readJSON(metaPath(id));
  if (!meta) return 'draft';
  if (meta.posted) return 'posted';

  const prompts = readJSON(promptsPath(id));
  const fr = listFramesSync(id);
  const outputs = listOutputsSync(id);

  if (outputs.length >= FRAME_COUNT) return 'ready';
  if (outputs.length > 0) return 'generating';
  if (prompts && prompts.frames?.every(f => f.prompt?.trim())) return 'prompts';
  if (fr.length >= FRAME_COUNT) return 'storyboard';
  return 'draft';
}

function listFramesSync(id) {
  const dir = framesDir(id);
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(f => /\.(png|jpe?g|webp)$/i.test(f))
    .sort()
    .map(f => path.join(dir, f));
}
function listOutputsSync(id) {
  const dir = outputDir(id);
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter(f => /\.(mp4|webm|mov)$/i.test(f))
    .sort()
    .map(f => path.join(dir, f));
}

function register(ipcMain) {
  ipcMain.handle('episodes:list', () => {
    const root = ensureRoot();
    return fs.readdirSync(root, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => {
        const m = readJSON(path.join(root, d.name, 'meta.json'));
        if (!m) return null;
        return { ...m, status: computeStatus(d.name) };
      })
      .filter(Boolean)
      .sort((a, b) => (b.scheduledFor || '').localeCompare(a.scheduledFor || ''));
  });

  ipcMain.handle('episodes:get', (_e, id) => {
    const meta = readJSON(metaPath(id));
    if (!meta) return null;
    const prompts = readJSON(promptsPath(id));
    const frames = listFramesSync(id);
    const outputs = listOutputsSync(id);
    const voice = fs.existsSync(voicePath(id)) ? fs.readFileSync(voicePath(id), 'utf-8') : null;
    return {
      meta: { ...meta, status: computeStatus(id) },
      prompts,
      frames,
      outputs,
      voice,
      paths: {
        root: path.join(projectsRoot(), id),
        frames: framesDir(id),
        output: outputDir(id),
        prompts: promptsPath(id),
        meta: metaPath(id),
        voice: voicePath(id)
      }
    };
  });

  ipcMain.handle('episodes:create', (_e, data) => {
    const id = `ep_${new Date().toISOString().slice(0,10).replace(/-/g,'')}_${slugify(data.title)}`.slice(0, 60);
    ensureRoot();
    const dir = path.join(projectsRoot(), id);
    fs.mkdirSync(dir, { recursive: true });
    fs.mkdirSync(path.join(dir, 'frames'), { recursive: true });
    fs.mkdirSync(path.join(dir, 'output'), { recursive: true });

    const meta = defaultMeta(id, data.title, data.scheduledFor);
    meta.storyIntent = data.storyIntent || '';
    writeJSON(metaPath(id), meta);

    const prompts = defaultPrompts();
    prompts.story_title = data.title || 'Untitled';
    writeJSON(promptsPath(id), prompts);

    return { ...meta, status: computeStatus(id) };
  });

  ipcMain.handle('episodes:update', (_e, id, patch) => {
    const meta = readJSON(metaPath(id));
    if (!meta) throw new Error('Episode not found: ' + id);
    const next = { ...meta, ...patch, updatedAt: new Date().toISOString() };
    writeJSON(metaPath(id), next);
    return { ...next, status: computeStatus(id) };
  });

  ipcMain.handle('episodes:remove', (_e, id) => {
    const dir = path.join(projectsRoot(), id);
    if (fs.existsSync(dir)) fs.rmSync(dir, { recursive: true, force: true });
    return true;
  });

  ipcMain.handle('episodes:importImages', (_e, id, sourcePaths) => {
    const dest = framesDir(id);
    fs.mkdirSync(dest, { recursive: true });
    const sorted = [...sourcePaths].sort();
    const imported = [];
    sorted.forEach((src, i) => {
      const ext = path.extname(src).toLowerCase() || '.png';
      const out = path.join(dest, `${String(i + 1).padStart(2, '0')}${ext}`);
      fs.copyFileSync(src, out);
      imported.push(out);
    });
    return imported;
  });

  ipcMain.handle('episodes:importSlices', (_e, id, dataUrls) => {
    const dest = framesDir(id);
    fs.mkdirSync(dest, { recursive: true });
    const imported = [];
    dataUrls.forEach((dataUrl, i) => {
      const m = /^data:image\/(png|jpeg|webp);base64,(.+)$/.exec(dataUrl);
      if (!m) return;
      const ext = m[1] === 'jpeg' ? '.jpg' : `.${m[1]}`;
      const out = path.join(dest, `${String(i + 1).padStart(2, '0')}${ext}`);
      fs.writeFileSync(out, Buffer.from(m[2], 'base64'));
      imported.push(out);
    });
    return imported;
  });

  ipcMain.handle('episodes:listFrames', (_e, id) => listFramesSync(id));
  ipcMain.handle('episodes:listOutputs', (_e, id) => listOutputsSync(id));

  ipcMain.handle('episodes:readFile', (_e, filePath) => {
    if (!filePath || !fs.existsSync(filePath)) return null;
    return fs.readFileSync(filePath, 'utf-8');
  });

  ipcMain.handle('episodes:writeJSON', (_e, id, name, data) => {
    const file = path.join(projectsRoot(), id, name);
    writeJSON(file, data);
    return true;
  });
}

module.exports = { register, FRAME_COUNT };
