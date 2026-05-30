import { useState } from 'react';
import { useStore } from '../../lib/store.js';
import SliceGridModal from '../SliceGridModal.jsx';
import { fileUrl } from '../../lib/fileUrl.js';

export default function StepImages({ episode }) {
  const refreshEpisodes = useStore(s => s.refreshEpisodes);
  const selectEpisode = useStore(s => s.selectEpisode);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [showSlicer, setShowSlicer] = useState(false);

  const frames = episode.frames || [];

  async function pickAndImport() {
    setErr(null);
    const files = await window.api.app.pickFiles({
      properties: ['openFile', 'multiSelections'],
      filters: [{ name: 'Images', extensions: ['png', 'jpg', 'jpeg', 'webp'] }]
    });
    if (!files || files.length === 0) return;
    if (files.length !== 10) {
      const ok = confirm(`You picked ${files.length} images. The pipeline expects 10. Import anyway?`);
      if (!ok) return;
    }
    setBusy(true);
    try {
      await window.api.episodes.importImages(episode.meta.id, files);
      await refreshEpisodes();
      await selectEpisode(episode.meta.id);
    } catch (e) {
      setErr(e.message || String(e));
    } finally { setBusy(false); }
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="card p-5">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h3 className="font-semibold text-text">Storyboard frames</h3>
            <p className="text-xs text-muted mt-1">Pick the 10 individual PNG/JPG panels (after slicing Banana's grid). They will be renamed 01-10 in order.</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowSlicer(true)} className="btn-primary disabled:opacity-50">
              ✂ Slice from grid
            </button>
            <button onClick={pickAndImport} disabled={busy} className="btn disabled:opacity-50">
              {busy ? 'Importing…' : 'Pick 10 PNGs'}
            </button>
          </div>
        </div>
        {err && <div className="text-sm text-red-400 mb-3">{err}</div>}

        {frames.length === 0 ? (
          <div className="border-2 border-dashed border-line rounded-md p-10 text-center text-sm">
            <div className="text-4xl mb-2">✂</div>
            <div className="text-text mb-1">No frames yet.</div>
            <div className="text-muted">Click <span className="text-text font-medium">Slice from grid</span> to import Banana's 5×2 storyboard image and auto-cut it into 10 frames.</div>
          </div>
        ) : (
          <div className="grid grid-cols-5 gap-3">
            {frames.map((p, i) => (
              <div key={p} className="relative rounded-md overflow-hidden border border-line bg-bg">
                <img src={fileUrl(p)} alt={`frame ${i+1}`} className="w-full aspect-[9/16] object-cover" />
                <div className="absolute top-1 left-1 bg-black/70 text-xs px-1.5 py-0.5 rounded">{String(i+1).padStart(2,'0')}</div>
              </div>
            ))}
          </div>
        )}
        {frames.length > 0 && frames.length < 10 && (
          <div className="text-xs text-amber-400 mt-3">⚠ Only {frames.length} frames found. Pipeline expects 10.</div>
        )}
      </div>

      {showSlicer && <SliceGridModal episodeId={episode.meta.id} onClose={() => setShowSlicer(false)} />}
    </div>
  );
}
