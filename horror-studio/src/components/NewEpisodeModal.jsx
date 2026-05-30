import { useState } from 'react';
import { useStore } from '../lib/store.js';
import { todayISO } from '../lib/status.js';

export default function NewEpisodeModal({ onClose }) {
  const createEpisode = useStore(s => s.createEpisode);
  const [title, setTitle] = useState('');
  const [scheduledFor, setScheduledFor] = useState(todayISO());
  const [storyIntent, setStoryIntent] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!title.trim()) return;
    setBusy(true);
    try {
      await createEpisode({ title: title.trim(), scheduledFor, storyIntent });
      onClose();
    } finally { setBusy(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <form onClick={e => e.stopPropagation()} onSubmit={submit}
        className="card w-full max-w-lg p-6 space-y-4">
        <h2 className="text-lg font-semibold">New episode</h2>

        <div>
          <label className="label">Title</label>
          <input className="input mt-1" autoFocus value={title} onChange={e => setTitle(e.target.value)}
            placeholder="e.g. The Babysitter - Hide and Seek" />
        </div>

        <div>
          <label className="label">Scheduled for</label>
          <input type="date" className="input mt-1" value={scheduledFor} onChange={e => setScheduledFor(e.target.value)} />
        </div>

        <div>
          <label className="label">Story intent (optional, you can edit later)</label>
          <textarea className="input mt-1 min-h-[100px]" value={storyIntent} onChange={e => setStoryIntent(e.target.value)}
            placeholder="A college babysitter alone with a 6-year-old plays one round of hide-and-seek..." />
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="btn">Cancel</button>
          <button type="submit" disabled={busy || !title.trim()} className="btn-primary disabled:opacity-50">
            {busy ? 'Creating…' : 'Create episode'}
          </button>
        </div>
      </form>
    </div>
  );
}
