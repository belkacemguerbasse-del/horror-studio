import { useState } from 'react';
import { useStore } from '../../lib/store.js';
import { buildBananaImagePrompt, buildBananaTextPrompt } from '../../lib/bananaPrompt.js';

export default function StepStory({ episode }) {
  const updateEpisode = useStore(s => s.updateEpisode);
  const refreshEpisodes = useStore(s => s.refreshEpisodes);
  const settings = useStore(s => s.settings);
  const [intent, setIntent] = useState(episode.meta.storyIntent || '');
  const [copiedImg, setCopiedImg] = useState(false);
  const [copiedTxt, setCopiedTxt] = useState(false);
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState('image'); // image | text

  const visualStyle = settings?.visualStyle || '';

  async function save() {
    setSaving(true);
    try {
      await updateEpisode(episode.meta.id, { storyIntent: intent });
      await refreshEpisodes();
    } finally { setSaving(false); }
  }

  async function copyImagePrompt() {
    await window.api.app.copyToClipboard(buildBananaImagePrompt(intent, visualStyle));
    await updateEpisode(episode.meta.id, { bananaPromptCopied: true });
    setCopiedImg(true);
    setTimeout(() => setCopiedImg(false), 2500);
  }

  async function copyTextPrompt() {
    await window.api.app.copyToClipboard(buildBananaTextPrompt(intent));
    setCopiedTxt(true);
    setTimeout(() => setCopiedTxt(false), 2500);
  }

  const previewText = preview === 'image' ? buildBananaImagePrompt(intent, visualStyle) : buildBananaTextPrompt(intent);

  return (
    <div className="space-y-6 max-w-4xl">
      <Section title="Story intent" desc="The core horror pitch. Be specific about character, setting, tone, and the twist — this is what shapes both the visuals and the narration.">
        <textarea className="input min-h-[180px] font-mono text-xs leading-relaxed"
          value={intent} onChange={e => setIntent(e.target.value)}
          placeholder="A college-age babysitter spends the evening alone with a 6-year-old girl..." />
        <div className="flex justify-end gap-2 mt-2">
          <button onClick={save} disabled={saving} className="btn">{saving ? 'Saving…' : 'Save'}</button>
        </div>
      </Section>

      <Section title="Banana 2 — two-pass workflow"
        desc="Banana often skips the image when the prompt mixes image + text. Use TWO separate Banana calls — they can run in parallel in two browser tabs.">

        <div className="grid grid-cols-2 gap-3 mb-4">
          <PassCard
            number="A"
            title="Image only"
            color="border-blood/60 bg-blood/5"
            desc="Generates ONLY the 10-panel 5×2 storyboard image. Short prompt → Banana reliably outputs the image."
            copied={copiedImg}
            onCopy={copyImagePrompt}
            onPreview={() => setPreview('image')}
            active={preview === 'image'}
          />
          <PassCard
            number="B"
            title="Motion prompts + Voice-over"
            color="border-sky-700/60 bg-sky-950/20"
            desc="Generates the 10 motion prompts AND the 10 VO lines from the Story Intent. No image needed."
            copied={copiedTxt}
            onCopy={copyTextPrompt}
            onPreview={() => setPreview('text')}
            active={preview === 'text'}
          />
        </div>

        <div className="border border-line rounded-md">
          <div className="px-3 py-2 border-b border-line text-xs uppercase tracking-wider text-muted flex items-center justify-between">
            <span>Preview · {preview === 'image' ? 'Pass A — Image prompt' : 'Pass B — Text prompt'}</span>
            <span className="font-mono">{previewText.length} chars</span>
          </div>
          <pre className="text-xs bg-bg p-3 whitespace-pre-wrap max-h-[400px] overflow-y-auto font-mono leading-relaxed text-ghost">{previewText}</pre>
        </div>

        <div className="mt-3 text-xs text-muted">
          <div className="font-semibold text-text mb-1">Recommended flow:</div>
          <ol className="list-decimal list-inside space-y-1 text-muted">
            <li>Copy <span className="text-blood">Pass A</span> → open Banana in tab 1 → paste → get the image</li>
            <li>In parallel, copy <span className="text-sky-400">Pass B</span> → open Banana in tab 2 → paste → get motion prompts + VO</li>
            <li>Save the image, paste motion prompts in Step 3, paste VO in Step 5</li>
          </ol>
        </div>
      </Section>
    </div>
  );
}

function PassCard({ number, title, color, desc, copied, onCopy, onPreview, active }) {
  return (
    <div className={`border-2 rounded-md p-4 transition cursor-pointer ${color} ${active ? 'ring-2 ring-text/10' : 'opacity-90 hover:opacity-100'}`}
      onClick={onPreview}>
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="text-xs uppercase tracking-wider text-muted">Pass {number}</div>
          <div className="font-semibold text-text">{title}</div>
        </div>
      </div>
      <p className="text-xs text-ghost mb-3">{desc}</p>
      <button onClick={(e) => { e.stopPropagation(); onCopy(); }} className="btn-primary w-full">
        {copied ? '✓ Copied' : `📋 Copy Pass ${number}`}
      </button>
    </div>
  );
}

function Section({ title, desc, children }) {
  return (
    <div className="card p-5">
      <div className="mb-3">
        <h3 className="font-semibold text-text">{title}</h3>
        {desc && <p className="text-xs text-muted mt-1">{desc}</p>}
      </div>
      {children}
    </div>
  );
}
