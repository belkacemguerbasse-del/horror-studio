import { useState, useEffect } from 'react';
import { useStore } from '../../lib/store.js';
import { fileUrl } from '../../lib/fileUrl.js';

export default function StepPrompts({ episode }) {
  const refreshEpisodes = useStore(s => s.refreshEpisodes);
  const selectEpisode = useStore(s => s.selectEpisode);
  const [data, setData] = useState(episode.prompts || null);
  const [saving, setSaving] = useState(false);
  const [bulk, setBulk] = useState('');

  useEffect(() => { setData(episode.prompts); }, [episode.meta.id]);

  if (!data) return <div className="text-muted">No prompts file yet.</div>;

  function updateFrame(i, patch) {
    const frames = data.frames.map((f, idx) => idx === i ? { ...f, ...patch } : f);
    setData({ ...data, frames });
  }

  async function save() {
    setSaving(true);
    try {
      await window.api.episodes.writeJSON(episode.meta.id, 'prompts.json', data);
      await refreshEpisodes();
      await selectEpisode(episode.meta.id);
    } finally { setSaving(false); }
  }

  function parseBulk() {
    // Accepts: numbered lines "1. ...", "Frame 1: ...", JSON array, or 10 blocks separated by blank lines
    const trimmed = bulk.trim();
    if (!trimmed) return;
    let lines = [];

    try {
      const json = JSON.parse(trimmed);
      if (Array.isArray(json)) {
        lines = json.slice(0, 10).map((x, i) => ({ id: String(i+1).padStart(2,'0'), text: typeof x === 'string' ? x : x.text || x.prompt || '' }));
      }
    } catch {}

    if (lines.length === 0) {
      const blocks = trimmed.split(/\n\s*\n/).filter(Boolean);
      if (blocks.length >= 10) {
        lines = blocks.slice(0, 10).map((b, i) => ({ id: String(i+1).padStart(2,'0'), text: b.replace(/^(?:frame\s*)?\d+[\.:\)]\s*/i, '').trim() }));
      }
    }

    if (lines.length === 0) {
      const rows = trimmed.split('\n').map(l => l.trim()).filter(Boolean);
      const numbered = rows.filter(r => /^(?:frame\s*)?\d+[\.:\)]/i.test(r));
      const src = numbered.length >= 10 ? numbered : rows;
      lines = src.slice(0, 10).map((r, i) => ({ id: String(i+1).padStart(2,'0'), text: r.replace(/^(?:frame\s*)?\d+[\.:\)]\s*/i, '').trim() }));
    }

    if (lines.length === 0) return;
    const frames = data.frames.map((f, i) => lines[i] ? { ...f, prompt: lines[i].text } : f);
    setData({ ...data, frames });
    setBulk('');
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="card p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-semibold text-text">Bulk paste from Banana</h3>
            <p className="text-xs text-muted mt-1">Paste the 10 motion prompts here (numbered list, JSON array, or 10 blocks).</p>
          </div>
          <button onClick={parseBulk} className="btn">Parse & fill</button>
        </div>
        <textarea className="input min-h-[140px] font-mono text-xs"
          value={bulk} onChange={e => setBulk(e.target.value)}
          placeholder="1. The babysitter slowly lowers her hands from her eyes...&#10;2. She takes one slow, deliberate step..." />
      </div>

      <div className="card p-5">
        <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
          <Field label="Width"    value={data.width}    onChange={v => setData({ ...data, width: Number(v) })} />
          <Field label="Height"   value={data.height}   onChange={v => setData({ ...data, height: Number(v) })} />
          <Field label="FPS"      value={data.fps}      onChange={v => setData({ ...data, fps: Number(v) })} />
        </div>

        <div className="space-y-3">
          {data.frames.map((f, i) => (
            <div key={f.id} className="border border-line rounded-md p-3 flex gap-3">
              <div className="w-24 shrink-0">
                {episode.frames[i] ? (
                  <img src={fileUrl(episode.frames[i])} className="rounded aspect-[9/16] object-cover w-full" />
                ) : (
                  <div className="aspect-[9/16] w-full bg-bg border border-line rounded flex items-center justify-center text-xs text-muted">no img</div>
                )}
              </div>
              <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-mono text-muted">frame {f.id}</div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-muted">duration</span>
                    <input type="number" value={f.duration} onChange={e => updateFrame(i, { duration: Number(e.target.value) })}
                      className="input w-16 text-center" min={1} max={20} />
                    <span className="text-muted">s</span>
                  </div>
                </div>
                <textarea className="input min-h-[70px] text-xs"
                  value={f.prompt} onChange={e => updateFrame(i, { prompt: e.target.value })}
                  placeholder="Subject action. Camera move. Ambient sound + diegetic cue. Atmospheric detail." />
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between mt-4 pt-4 border-t border-line">
          <div className="text-xs text-muted">
            Total : {data.frames.reduce((a, f) => a + (f.duration || 0), 0)}s
          </div>
          <button onClick={save} disabled={saving} className="btn-primary">{saving ? 'Saving…' : 'Save prompts.json'}</button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, onChange }) {
  return (
    <div>
      <label className="label">{label}</label>
      <input className="input mt-1" value={value} onChange={e => onChange(e.target.value)} />
    </div>
  );
}
