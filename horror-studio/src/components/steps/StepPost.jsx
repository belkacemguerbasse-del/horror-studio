import { useState } from 'react';
import { useStore } from '../../lib/store.js';

export default function StepPost({ episode }) {
  const updateEpisode = useStore(s => s.updateEpisode);
  const [posted, setPosted] = useState(!!episode.meta.posted);
  const [tiktokUrl, setTiktokUrl] = useState(episode.meta.tiktokUrl || '');
  const [notes, setNotes] = useState(episode.meta.notes || '');
  const [saving, setSaving] = useState(false);

  async function save() {
    setSaving(true);
    try {
      await updateEpisode(episode.meta.id, {
        posted,
        postedAt: posted ? (episode.meta.postedAt || new Date().toISOString()) : null,
        tiktokUrl,
        notes
      });
    } finally { setSaving(false); }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="card p-5">
        <h3 className="font-semibold text-text mb-1">Publishing tracker</h3>
        <p className="text-xs text-muted mb-4">Track whether this episode is live on TikTok and keep the URL for later reference.</p>

        <label className="flex items-center gap-3 p-3 rounded-md bg-bg border border-line cursor-pointer hover:border-blood/40">
          <input type="checkbox" checked={posted} onChange={e => setPosted(e.target.checked)} className="w-4 h-4 accent-blood" />
          <div>
            <div className="font-medium text-text">Mark as posted</div>
            <div className="text-xs text-muted">{posted && episode.meta.postedAt ? `Posted at ${episode.meta.postedAt}` : 'Not posted yet'}</div>
          </div>
        </label>

        <div className="mt-4">
          <label className="label">TikTok URL</label>
          <input className="input mt-1" value={tiktokUrl} onChange={e => setTiktokUrl(e.target.value)}
            placeholder="https://www.tiktok.com/@you/video/..." />
        </div>

        <div className="mt-4">
          <label className="label">Notes</label>
          <textarea className="input mt-1 min-h-[100px]" value={notes} onChange={e => setNotes(e.target.value)}
            placeholder="Performance, audience reaction, ideas for next episode..." />
        </div>

        <div className="flex justify-end mt-4">
          <button onClick={save} disabled={saving} className="btn-primary">{saving ? 'Saving…' : 'Save'}</button>
        </div>
      </div>
    </div>
  );
}
