import { useState, useEffect } from 'react';
import { useStore } from '../lib/store.js';

export default function Settings() {
  const settings = useStore(s => s.settings);
  const saveSettings = useStore(s => s.saveSettings);
  const pingComfy = useStore(s => s.pingComfy);
  const comfyStatus = useStore(s => s.comfyStatus);
  const [form, setForm] = useState(settings || {});
  const [saving, setSaving] = useState(false);
  const [voices, setVoices] = useState([]);
  const [loadingVoices, setLoadingVoices] = useState(false);
  const [voicesErr, setVoicesErr] = useState(null);

  useEffect(() => { if (settings) setForm(settings); }, [settings]);

  if (!settings) return <div className="p-10 text-muted">Loading…</div>;

  function set(k, v) { setForm(prev => ({ ...prev, [k]: v })); }

  async function pickDir(key) {
    const d = await window.api.app.pickDir();
    if (d) set(key, d);
  }
  async function pickFile(key) {
    const f = await window.api.app.pickFiles({ properties: ['openFile'] });
    if (f && f[0]) set(key, f[0]);
  }

  async function save() {
    setSaving(true);
    try {
      await saveSettings(form);
      await pingComfy();
    } finally { setSaving(false); }
  }

  async function loadVoices() {
    setVoicesErr(null); setLoadingVoices(true); setVoices([]);
    try {
      await saveSettings({ elevenApiKey: (form.elevenApiKey || '').trim() });
      const v = await window.api.elevenlabs.voices();
      if (!v || v.length === 0) {
        setVoicesErr('No voices returned by ElevenLabs (account empty or API call returned 0 results).');
      } else {
        setVoices(v);
      }
    } catch (e) {
      setVoicesErr(e?.message || String(e));
      console.error('Load voices failed:', e);
    }
    finally { setLoadingVoices(false); }
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="px-8 py-6 border-b border-line">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-muted text-sm">All settings are stored locally.</p>
      </header>

      <div className="p-8 space-y-6 max-w-3xl">

        <Card title="ComfyUI" desc="The server that runs the LTX 2.3 video generation workflow.">
          <Row label="ComfyUI URL">
            <div className="flex gap-2">
              <input className="input" value={form.comfyUrl || ''} onChange={e => set('comfyUrl', e.target.value)} placeholder="http://127.0.0.1:8000" />
              <button onClick={pingComfy} className="btn shrink-0">Ping</button>
            </div>
            <div className="text-xs mt-1 flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${comfyStatus.ok ? 'bg-emerald-500' : 'bg-red-500'}`} />
              <span className="text-muted">{comfyStatus.ok ? 'online' : `offline — ${comfyStatus.error || ''}`}</span>
            </div>
          </Row>
        </Card>

        <Card title="Pipeline scripts" desc="Paths to the existing Python scripts that drive ComfyUI and ffmpeg.">
          <Row label="Python executable">
            <div className="flex gap-2">
              <input className="input" value={form.pythonExe || ''} onChange={e => set('pythonExe', e.target.value)} placeholder="python" />
              <button onClick={() => pickFile('pythonExe')} className="btn shrink-0">Browse</button>
            </div>
          </Row>
          <Row label="ffmpeg.exe (optional — leave empty to use PATH)">
            <div className="flex gap-2">
              <input className="input font-mono text-xs" value={form.ffmpegPath || ''} onChange={e => set('ffmpegPath', e.target.value)} placeholder="C:\\ffmpeg\\bin\\ffmpeg.exe" />
              <button onClick={() => pickFile('ffmpegPath')} className="btn shrink-0">Browse</button>
            </div>
            <div className="text-xs text-muted mt-1">Use this if ffmpeg is not in your PATH (portable install).</div>
          </Row>
          <Row label="generate_batch.py">
            <div className="flex gap-2">
              <input className="input font-mono text-xs" value={form.generateScript || ''} onChange={e => set('generateScript', e.target.value)} />
              <button onClick={() => pickFile('generateScript')} className="btn shrink-0">Browse</button>
            </div>
          </Row>
          <Row label="concat_final.py">
            <div className="flex gap-2">
              <input className="input font-mono text-xs" value={form.concatScript || ''} onChange={e => set('concatScript', e.target.value)} />
              <button onClick={() => pickFile('concatScript')} className="btn shrink-0">Browse</button>
            </div>
          </Row>
          <Row label="Projects root folder">
            <div className="flex gap-2">
              <input className="input font-mono text-xs" value={form.projectsRoot || ''} onChange={e => set('projectsRoot', e.target.value)} />
              <button onClick={() => pickDir('projectsRoot')} className="btn shrink-0">Browse</button>
            </div>
          </Row>
        </Card>

        <Card title="ElevenLabs" desc="API key + default voice for the voice-over generation.">
          <Row label="API key">
            <input className="input" type="password" value={form.elevenApiKey || ''} onChange={e => set('elevenApiKey', e.target.value)} placeholder="sk_..." />
          </Row>
          <Row label="Default voice">
            <div className="flex gap-2">
              <select className="input" value={form.elevenVoiceId || ''} onChange={e => set('elevenVoiceId', e.target.value)}>
                <option value="">— select a voice —</option>
                {voices.map(v => <option key={v.voice_id} value={v.voice_id}>{v.name}</option>)}
              </select>
              <button onClick={loadVoices} disabled={loadingVoices || !form.elevenApiKey} className="btn shrink-0">
                {loadingVoices ? 'Loading…' : 'Load voices'}
              </button>
            </div>
            {voicesErr && <div className="text-xs text-red-400 mt-1">{voicesErr}</div>}
          </Row>

          <Row label="Default model">
            <select className="input" value={form.elevenModelId || 'eleven_multilingual_v2'} onChange={e => set('elevenModelId', e.target.value)}>
              <option value="eleven_v3">v3 (alpha) — top quality + emotional tags</option>
              <option value="eleven_multilingual_v2">Multilingual v2 — stable, long-form (default)</option>
              <option value="eleven_turbo_v2_5">Turbo v2.5 — balanced quality/speed</option>
              <option value="eleven_flash_v2_5">Flash v2.5 — ultra-low latency</option>
            </select>
          </Row>

          <Row label="Default language">
            <select className="input" value={form.elevenLanguage || 'auto'} onChange={e => set('elevenLanguage', e.target.value)}>
              <option value="auto">Auto-detect</option>
              <option value="en">English</option>
              <option value="fr">Français</option>
              <option value="es">Español</option>
              <option value="de">Deutsch</option>
              <option value="it">Italiano</option>
              <option value="pt">Português</option>
              <option value="pl">Polski</option>
              <option value="ja">日本語</option>
              <option value="zh">中文</option>
            </select>
          </Row>

          <Row label="Request stitching">
            <label className="flex items-center gap-3 p-2 rounded-md bg-bg border border-line cursor-pointer hover:border-blood/40">
              <input type="checkbox" checked={!!form.elevenUseStitching}
                onChange={e => set('elevenUseStitching', e.target.checked)}
                className="w-4 h-4 accent-blood" />
              <div>
                <div className="text-sm text-text">Enabled by default</div>
                <div className="text-xs text-muted">Passes each line's neighbours as context — eliminates tonal jumps between the 10 audio clips.</div>
              </div>
            </label>
          </Row>
        </Card>

        <Card title="Visual style preset" desc="Injected into every Banana image prompt. Define your channel's signature look here — characters, lighting, color palette, references.">
          <textarea
            className="input font-mono text-xs leading-relaxed min-h-[300px]"
            value={form.visualStyle || ''}
            onChange={e => set('visualStyle', e.target.value)}
            placeholder="Describe the consistent visual style for all generated storyboards..."
          />
          <div className="text-xs text-muted mt-2">
            Tip: Mention concrete references (Laika Studios, Tim Burton, etc.), character proportions, color palette, lighting, and what to AVOID. The more specific, the more consistent the output.
          </div>
        </Card>

        <Card title="Defaults for new episodes">
          <div className="grid grid-cols-4 gap-3">
            <Row label="Width">  <input type="number" className="input" value={form.defaultWidth || 720}  onChange={e => set('defaultWidth', Number(e.target.value))} /></Row>
            <Row label="Height"> <input type="number" className="input" value={form.defaultHeight || 1280} onChange={e => set('defaultHeight', Number(e.target.value))} /></Row>
            <Row label="FPS">    <input type="number" className="input" value={form.defaultFps || 25}    onChange={e => set('defaultFps', Number(e.target.value))} /></Row>
            <Row label="Duration (s)"><input type="number" className="input" value={form.defaultDuration || 7} onChange={e => set('defaultDuration', Number(e.target.value))} /></Row>
          </div>
        </Card>

        <div className="flex justify-end gap-2">
          <button onClick={save} disabled={saving} className="btn-primary">{saving ? 'Saving…' : 'Save settings'}</button>
        </div>
      </div>
    </div>
  );
}

function Card({ title, desc, children }) {
  return (
    <div className="card p-5">
      <div className="mb-3">
        <h3 className="font-semibold text-text">{title}</h3>
        {desc && <p className="text-xs text-muted mt-1">{desc}</p>}
      </div>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div>
      <label className="label">{label}</label>
      <div className="mt-1">{children}</div>
    </div>
  );
}
