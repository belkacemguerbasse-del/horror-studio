import { useState, useEffect, useRef } from 'react';
import { useStore } from '../../lib/store.js';
import { fileUrl } from '../../lib/fileUrl.js';

export default function StepConcat({ episode }) {
  const { jobs, settings, saveSettings } = useStore();
  const job = jobs[episode.meta.id];
  const [busy, setBusy] = useState(false);
  const [finalPath, setFinalPath] = useState(null);
  const [voiceVol, setVoiceVol]     = useState(settings?.voiceVolume   ?? 1.10);
  const [ambientVol, setAmbientVol] = useState(settings?.ambientVolume ?? 0.25);
  const [noVoice, setNoVoice]       = useState(false);
  const logRef = useRef(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [job?.logs?.length]);

  useEffect(() => {
    const text = job?.logs?.join('') || '';
    const m = text.match(/\[OK\] Final video:\s*(.+\.mp4)\s/);
    if (m) setFinalPath(m[1].trim());
  }, [job?.logs?.length]);

  async function concat() {
    setBusy(true); setFinalPath(null);
    try {
      await saveSettings({ voiceVolume: voiceVol, ambientVolume: ambientVol });
      await window.api.pipeline.concat(episode.meta.id, {
        voiceVolume: voiceVol,
        ambientVolume: ambientVol,
        noVoice
      });
    } finally { setTimeout(() => setBusy(false), 500); }
  }

  const outputs = episode.outputs || [];
  const isRunning = job && !job.done && job.kind === 'concat';

  // Count available voice files via paths
  const voicePath = episode.paths?.root ? `${episode.paths.root}\\voice` : null;
  // We don't have a direct count from the API; the script log will report it.

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="card p-5">
        <h3 className="font-semibold text-text mb-1">Final concat (ffmpeg)</h3>
        <p className="text-xs text-muted mb-4">
          Mixes each generated clip with its matching voice-over file (<span className="font-mono">voice/01.mp3 ...</span>), then assembles all clips into one 9:16 TikTok-ready MP4.
        </p>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-muted uppercase tracking-wider">Voice volume</span>
              <span className="font-mono text-ghost">{voiceVol.toFixed(2)}</span>
            </div>
            <input type="range" min={0} max={2} step={0.05}
              value={voiceVol} onChange={e => setVoiceVol(parseFloat(e.target.value))}
              disabled={noVoice}
              className="w-full accent-blood disabled:opacity-40" />
            <div className="text-[10px] text-muted">1.0 = original level · 1.10 recommended</div>
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-muted uppercase tracking-wider">Ambient (LTX audio) volume</span>
              <span className="font-mono text-ghost">{ambientVol.toFixed(2)}</span>
            </div>
            <input type="range" min={0} max={1} step={0.05}
              value={ambientVol} onChange={e => setAmbientVol(parseFloat(e.target.value))}
              className="w-full accent-blood" />
            <div className="text-[10px] text-muted">Keep LTX wind/footsteps/music box under the voice. 0.25 recommended.</div>
          </div>
        </div>

        <label className="flex items-center gap-2 text-xs text-muted mb-4 cursor-pointer">
          <input type="checkbox" checked={noVoice} onChange={e => setNoVoice(e.target.checked)} className="accent-blood" />
          <span>Skip voice-over mixing (use only original LTX audio)</span>
        </label>

        <div className="flex items-center gap-2">
          <button onClick={concat} disabled={busy || isRunning || outputs.length === 0} className="btn-primary disabled:opacity-50">
            {isRunning ? 'Encoding…' : '🎞 Concat final video'}
          </button>
          {outputs.length < 10 && <div className="text-xs text-amber-400">Only {outputs.length}/10 clips ready</div>}
        </div>
      </div>

      {job && job.kind === 'concat' && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-text">FFmpeg log</h3>
            <div className="text-xs text-muted">{job.done ? `exit ${job.code}` : 'running'}</div>
          </div>
          <pre ref={logRef} className="bg-bg border border-line rounded-md p-3 text-xs font-mono leading-relaxed text-ghost max-h-[400px] overflow-y-auto whitespace-pre-wrap">
            {job.logs.join('')}
          </pre>
        </div>
      )}

      {finalPath && (
        <div className="card p-5">
          <h3 className="font-semibold text-text mb-3">Preview final video</h3>
          <video src={fileUrl(finalPath)} controls className="w-full max-w-[400px] mx-auto rounded border border-line" />
          <div className="flex justify-center gap-2 mt-3">
            <button onClick={() => window.api.app.showItem(finalPath)} className="btn">📂 Show in folder</button>
          </div>
        </div>
      )}
    </div>
  );
}
