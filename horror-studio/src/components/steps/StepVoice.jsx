import { useState, useEffect } from 'react';
import { useStore } from '../../lib/store.js';

const DEFAULT_LINES = [
  'For thirteen years, she had drawn the same man, every single night.',
  'Her mother had called it an obsession. She called it remembering.',
  'On that quiet evening, she finished his eyes. The ink ran green.',
  'The chair behind her scraped against the floor. She had not moved it.',
  'He had always stood at that window. She had only stopped looking.',
  'Her hand trembled. His did not. He had been waiting longer than she had.',
  'She knew the way out. She walked toward the stairs instead.',
  'His fingers found the wood before she heard the step.',
  'She had drawn him exactly. Every joint. Every shadow. Every kindness.',
  'He had come for her. She had been hoping he would.'
];

const MODELS = [
  { id: 'eleven_v3',              label: 'v3 (alpha)',         tagline: 'Top quality + emotional tags · 70+ langs',     supportsTags: true,  supportsLang: true  },
  { id: 'eleven_multilingual_v2', label: 'Multilingual v2',    tagline: 'Stable, great for long-form · 29 langs',       supportsTags: false, supportsLang: true  },
  { id: 'eleven_turbo_v2_5',      label: 'Turbo v2.5',         tagline: 'Balanced quality/speed · 32 langs',            supportsTags: false, supportsLang: true  },
  { id: 'eleven_flash_v2_5',      label: 'Flash v2.5',         tagline: 'Ultra-low latency (~75ms) · 32 langs',         supportsTags: false, supportsLang: true  }
];

const LANGUAGES = [
  { code: 'auto', label: 'Auto-detect' },
  { code: 'en',   label: 'English' },
  { code: 'fr',   label: 'Français' },
  { code: 'es',   label: 'Español' },
  { code: 'de',   label: 'Deutsch' },
  { code: 'it',   label: 'Italiano' },
  { code: 'pt',   label: 'Português' },
  { code: 'pl',   label: 'Polski' },
  { code: 'ja',   label: '日本語' },
  { code: 'zh',   label: '中文' }
];

const V3_PRESETS = [
  { id: 'creative', label: 'Creative', stability: 0.10, hint: 'Expressive, more emotional variation, may hallucinate' },
  { id: 'natural',  label: 'Natural',  stability: 0.50, hint: 'Balanced — closest to reference, recommended' },
  { id: 'robust',   label: 'Robust',   stability: 0.85, hint: 'Stable, less responsive to tags' }
];

const HORROR_TAGS = [
  '[whispers]', '[sighs]', '[exhales]', '[long pause]', '[soft]', '[trembling]',
  '[crying]', '[gasp]', '[hushed]', '[breathes]', '[cold]', '[flat]'
];

function buildVoFallbackPrompt(episode) {
  const intent = episode?.meta?.storyIntent || '[Story intent not set]';
  const prompts = episode?.prompts?.frames || [];
  const promptLines = prompts.length
    ? prompts.map(f => `Frame ${f.id}: ${f.prompt || '(empty)'}`).join('\n')
    : '(No motion prompts yet)';

  return `You are writing the THIRD-PERSON OMNISCIENT voice-over for a 70-second horror TikTok video composed of 10 clips of 7 seconds each.

This is an external storyteller narrating the events — like a Tales from the Crypt narrator, a creepypasta read aloud, an Edgar Allan Poe narration, or a calm true-crime podcast host telling a chilling case. NOT the character speaking. The character NEVER talks. The narrator KNOWS more than the character.

### Rules
- Third-person past tense ("She walked toward the door", NEVER "I walked")
- Refer to the protagonist as "she" / "he" / "they" — or by first name if provided in the Story Intent
- The narrator can foreshadow ("She did not know it would be the last door she opened")
- Each line ~10-15 words, ~6 seconds spoken at 125 wpm
- Slow, measured, slightly menacing — no exclamations, no "suddenly", no quoted dialogue, no theatrical phrasing
- Do NOT describe what the camera already shows — instead reveal context, history, the character's hidden thoughts, or what the audience cannot see
- Arc: lines 1-2 calm setup of the character's world, 3-5 the narrator hints something is wrong, 6-7 confirmation, 8-9 restrained dread (5-8 words), line 10 cold final statement that delivers the twist/fate

### Output format
VO 01: ...
VO 02: ...
...
VO 10: ...

### Story Intent
${intent}

### Motion prompts of the 10 clips (context only)
${promptLines}
`;
}

export default function StepVoice({ episode }) {
  const settings = useStore(s => s.settings);
  const saveSettings = useStore(s => s.saveSettings);

  const [lines, setLines]         = useState(() => Array.from({ length: 10 }, (_, i) => ({
    id: String(i + 1).padStart(2, '0'),
    text: DEFAULT_LINES[i] || ''
  })));
  const [voices, setVoices]       = useState([]);
  const [voiceId, setVoiceId]     = useState('');
  const [modelId, setModelId]     = useState('eleven_multilingual_v2');
  const [language, setLanguage]   = useState('auto');
  const [useStitching, setStitch] = useState(true);
  const [stability, setStability] = useState(0.5);
  const [v3Preset, setV3Preset]   = useState('natural');
  const [similarity, setSimilarity] = useState(0.75);
  const [style, setStyle]         = useState(0.45);
  const [busy, setBusy]           = useState(false);
  const [err, setErr]             = useState(null);
  const [result, setResult]       = useState(null);
  const [bulk, setBulk]           = useState('');
  const [voCopied, setVoCopied]   = useState(false);
  const [focusedLine, setFocusedLine] = useState(null);

  useEffect(() => {
    if (!settings) return;
    if (settings.elevenVoiceId)    setVoiceId(settings.elevenVoiceId);
    if (settings.elevenModelId)    setModelId(settings.elevenModelId);
    if (settings.elevenLanguage)   setLanguage(settings.elevenLanguage);
    if (typeof settings.elevenUseStitching === 'boolean') setStitch(settings.elevenUseStitching);
  }, [settings?.elevenVoiceId, settings?.elevenModelId, settings?.elevenLanguage]);

  const model = MODELS.find(m => m.id === modelId) || MODELS[1];
  const isV3 = model.supportsTags;

  // Sync v3 preset -> stability
  useEffect(() => {
    if (isV3) {
      const preset = V3_PRESETS.find(p => p.id === v3Preset);
      if (preset) setStability(preset.stability);
    }
  }, [v3Preset, isV3]);

  async function loadVoices() {
    setErr(null);
    try {
      const v = await window.api.elevenlabs.voices();
      setVoices(v);
      if (!voiceId && v.length) setVoiceId(v[0].voice_id);
    } catch (e) { setErr(e.message); }
  }

  async function generate() {
    setErr(null); setBusy(true); setResult(null);
    try {
      const r = await window.api.elevenlabs.generate(episode.meta.id, {
        voiceId, modelId, language, useStitching,
        stability, similarity, style,
        lines
      });
      setResult(r);
      // Remember the user's choices
      saveSettings({ elevenModelId: modelId, elevenLanguage: language, elevenUseStitching: useStitching });
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  }

  function insertTag(tag) {
    if (focusedLine === null) return;
    const cur = lines[focusedLine];
    const next = [...lines];
    next[focusedLine] = { ...cur, text: (cur.text + ' ' + tag).trim() };
    setLines(next);
  }

  function parseBulk() {
    const trimmed = bulk.trim();
    if (!trimmed) return;
    let parsed = [];
    try {
      const json = JSON.parse(trimmed);
      if (Array.isArray(json)) {
        parsed = json.slice(0, 10).map((x, i) => ({
          id: String(i + 1).padStart(2, '0'),
          text: (typeof x === 'string' ? x : x.text || x.line || '').trim()
        }));
      }
    } catch {}
    if (parsed.length === 0) {
      const rows = trimmed.split('\n').map(l => l.trim()).filter(Boolean);
      const numbered = rows.filter(r => /^(?:vo\s*)?\d+[\.:\)]/i.test(r));
      const src = numbered.length >= 10 ? numbered : rows;
      parsed = src.slice(0, 10).map((r, i) => ({
        id: String(i + 1).padStart(2, '0'),
        text: r.replace(/^(?:vo\s*)?\d+[\.:\)]\s*/i, '').trim()
      }));
    }
    if (parsed.length === 0) return;
    const next = lines.map((l, i) => parsed[i] ? { ...l, text: parsed[i].text } : l);
    setLines(next);
    setBulk('');
  }

  async function copyVoFallbackPrompt() {
    const p = buildVoFallbackPrompt(episode);
    await window.api.app.copyToClipboard(p);
    setVoCopied(true);
    setTimeout(() => setVoCopied(false), 2500);
  }

  const hasKey = !!settings?.elevenApiKey;
  const totalChars = lines.reduce((a, l) => a + l.text.length, 0);
  // Pricing estimate: $0.30 per 1000 chars on Creator tier (rough average across plans)
  const estCostUSD = (totalChars / 1000) * 0.30;

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="card p-5">
        <h3 className="font-semibold text-text mb-1">ElevenLabs voice generation</h3>
        <p className="text-xs text-muted mb-4">10 MP3 files saved under the episode's <span className="font-mono">voice/</span> folder.</p>

        {!hasKey && <div className="text-sm text-amber-400 mb-3">⚠ Set your ElevenLabs API key in Settings first.</div>}

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="label">Voice</label>
            <div className="flex gap-2 mt-1">
              <select className="input" value={voiceId} onChange={e => setVoiceId(e.target.value)} disabled={!voices.length}>
                {!voices.length && <option value="">— load voices first —</option>}
                {voices.map(v => <option key={v.voice_id} value={v.voice_id}>{v.name}</option>)}
              </select>
              <button onClick={loadVoices} disabled={!hasKey} className="btn shrink-0">Load</button>
            </div>
          </div>

          <div>
            <label className="label">Model</label>
            <select className="input mt-1" value={modelId} onChange={e => setModelId(e.target.value)}>
              {MODELS.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
            </select>
            <div className="text-xs text-muted mt-1">{model.tagline}</div>
          </div>

          <div>
            <label className="label">Language</label>
            <select className="input mt-1" value={language} onChange={e => setLanguage(e.target.value)} disabled={!model.supportsLang}>
              {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
          </div>

          <div>
            <label className="label flex items-center gap-2">
              <input type="checkbox" checked={useStitching && !isV3} onChange={e => setStitch(e.target.checked)} disabled={isV3} className="accent-blood disabled:opacity-40" />
              Request Stitching {isV3 && <span className="text-amber-400 normal-case">(not supported on v3 yet)</span>}
            </label>
            <div className="text-xs text-muted mt-1">
              {isV3
                ? 'v3 does not yet support previous_text/next_text. Use v2 or Turbo if you need cross-clip continuity.'
                : 'Pass surrounding lines as context for seamless tonal continuity between clips.'}
            </div>
          </div>
        </div>

        {isV3 ? (
          <div className="mb-4">
            <label className="label">Stability preset (v3)</label>
            <div className="grid grid-cols-3 gap-2 mt-1">
              {V3_PRESETS.map(p => (
                <button key={p.id} onClick={() => setV3Preset(p.id)}
                  className={`p-2 rounded border text-left text-xs ${v3Preset === p.id ? 'border-blood bg-blood/10 text-text' : 'border-line bg-card text-ghost hover:border-line'}`}>
                  <div className="font-semibold">{p.label}</div>
                  <div className="text-[10px] text-muted leading-tight mt-0.5">{p.hint}</div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-3 mb-4">
            <Slider label="Stability"  value={stability}  onChange={setStability} />
            <Slider label="Similarity" value={similarity} onChange={setSimilarity} />
            <Slider label="Style"      value={style}      onChange={setStyle} />
          </div>
        )}

        {isV3 && (
          <div className="mb-4 p-3 rounded-md bg-blood/5 border border-blood/30">
            <div className="text-xs text-text font-semibold mb-2">v3 audio tags — click to insert in the focused line {focusedLine !== null ? `(line ${String(focusedLine + 1).padStart(2,'0')})` : ''}</div>
            <div className="flex flex-wrap gap-1">
              {HORROR_TAGS.map(t => (
                <button key={t} onClick={() => insertTag(t)} disabled={focusedLine === null}
                  className="text-xs font-mono px-1.5 py-0.5 rounded bg-bg border border-line text-ghost hover:border-blood/40 hover:text-text disabled:opacity-40 disabled:cursor-not-allowed">
                  {t}
                </button>
              ))}
            </div>
            <div className="text-[11px] text-muted mt-2">Use <span className="font-mono">...</span> for pauses · CAPITALIZE for emphasis. v3 ignores SSML break tags.</div>
          </div>
        )}

        <div className="flex items-center justify-between mb-2">
          <div className="text-xs text-muted">
            ~<span className="text-text font-semibold">{totalChars}</span> chars · est. <span className="text-text font-semibold">${estCostUSD.toFixed(3)}</span>
          </div>
          <button onClick={generate} disabled={busy || !hasKey || !voiceId} className="btn-primary disabled:opacity-50">
            {busy ? 'Generating…' : '🎙 Generate 10 voice lines'}
          </button>
        </div>
        {err && <div className="text-sm text-red-400 mt-3">{err}</div>}

        {result && (
          <div className="mt-4 p-3 rounded-md bg-emerald-950/30 border border-emerald-700/40 text-sm">
            <div className="text-emerald-400 font-semibold mb-1">✓ {result.results.length} files generated</div>
            <div className="text-xs text-ghost">
              {result.totalChars} chars billed · model: <span className="font-mono">{result.modelId}</span> · lang: <span className="font-mono">{result.language}</span>
              {result.useStitching && ' · stitched'}
            </div>
          </div>
        )}
      </div>

      <div className="card p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="font-semibold text-text">Bulk paste from Banana</h3>
            <p className="text-xs text-muted mt-1">Paste the <span className="font-mono">VO 01:</span> ... <span className="font-mono">VO 10:</span> block. If Banana left them empty, use the fallback prompt.</p>
          </div>
          <div className="flex gap-2">
            <button onClick={copyVoFallbackPrompt} className="btn">{voCopied ? '✓ Copied' : '📋 Copy VO-only prompt'}</button>
            <button onClick={parseBulk} className="btn-primary">Parse & fill</button>
          </div>
        </div>
        <textarea className="input min-h-[120px] font-mono text-xs"
          value={bulk} onChange={e => setBulk(e.target.value)}
          placeholder={`VO 01: For thirteen years, she had drawn the same man.\nVO 02: Her mother had called it an obsession.\n...`} />
      </div>

      <div className="card p-5">
        <h3 className="font-semibold text-text mb-3">Narration script</h3>
        <div className="space-y-2">
          {lines.map((l, i) => (
            <div key={l.id} className="flex gap-2">
              <div className="w-10 shrink-0 pt-2 text-xs font-mono text-muted text-right">{l.id}</div>
              <textarea className="input text-xs min-h-[50px]"
                value={l.text}
                onFocus={() => setFocusedLine(i)}
                onChange={e => {
                  const next = [...lines]; next[i] = { ...l, text: e.target.value }; setLines(next);
                }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Slider({ label, value, onChange }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-muted uppercase tracking-wider">{label}</span>
        <span className="font-mono text-ghost">{value.toFixed(2)}</span>
      </div>
      <input type="range" min={0} max={1} step={0.05} value={value} onChange={e => onChange(parseFloat(e.target.value))}
        className="w-full accent-blood" />
    </div>
  );
}
