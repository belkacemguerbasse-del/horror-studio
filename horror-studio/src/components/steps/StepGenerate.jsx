import { useState, useMemo, useEffect, useRef } from 'react';
import { useStore } from '../../lib/store.js';
import { fileUrl } from '../../lib/fileUrl.js';

export default function StepGenerate({ episode }) {
  const { jobs, comfyStatus } = useStore();
  const job = jobs[episode.meta.id];
  const [busy, setBusy] = useState(false);
  const [only, setOnly] = useState('');
  const logRef = useRef(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [job?.logs?.length]);

  const outputs = episode.outputs || [];
  const completed = new Set(outputs.map(p => p.match(/(\d{2})\.\w+$/)?.[1]).filter(Boolean));

  async function runAll() {
    setBusy(true);
    try { await window.api.pipeline.generate(episode.meta.id, {}); }
    finally { setTimeout(() => setBusy(false), 500); }
  }
  async function runOnly() {
    if (!only.trim()) return;
    setBusy(true);
    try { await window.api.pipeline.generate(episode.meta.id, { only: only.trim() }); }
    finally { setTimeout(() => setBusy(false), 500); }
  }

  const isRunning = job && !job.done;

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-text">Run LTX 2.3 generation</h3>
            <p className="text-xs text-muted mt-1">Sends each frame + prompt to ComfyUI sequentially. Logs appear below.</p>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className={`w-2 h-2 rounded-full ${comfyStatus.ok ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className="text-muted">ComfyUI {comfyStatus.ok ? 'online' : 'offline'}</span>
          </div>
        </div>

        <div className="grid grid-cols-10 gap-1.5 mb-4">
          {Array.from({ length: 10 }, (_, i) => {
            const id = String(i + 1).padStart(2, '0');
            const done = completed.has(id);
            return (
              <div key={id} className={`aspect-square rounded text-xs flex items-center justify-center font-mono border ${done ? 'bg-emerald-950/50 border-emerald-700/50 text-emerald-400' : 'bg-card border-line text-muted'}`}>
                {done ? '✓' : id}
              </div>
            );
          })}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button onClick={runAll} disabled={busy || isRunning || !comfyStatus.ok} className="btn-primary disabled:opacity-50">
            {isRunning ? 'Running…' : '▶ Generate all 10 clips'}
          </button>
          <div className="flex items-center gap-2 ml-auto">
            <input className="input w-28" placeholder="e.g. 03,07" value={only} onChange={e => setOnly(e.target.value)} />
            <button onClick={runOnly} disabled={busy || isRunning || !comfyStatus.ok || !only.trim()} className="btn disabled:opacity-50">▶ Regen frame(s)</button>
          </div>
          {isRunning && job?.jobId && (
            <button onClick={() => window.api.pipeline.cancel(job.jobId)} className="btn text-red-400">Cancel</button>
          )}
        </div>
      </div>

      {job && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold text-text">Job log</h3>
            <div className="text-xs text-muted">{job.done ? `exit ${job.code}` : 'running'}</div>
          </div>
          <pre ref={logRef} className="bg-bg border border-line rounded-md p-3 text-xs font-mono leading-relaxed text-ghost max-h-[400px] overflow-y-auto whitespace-pre-wrap">
            {job.logs.join('')}
          </pre>
        </div>
      )}

      {outputs.length > 0 && (
        <div className="card p-5">
          <h3 className="font-semibold text-text mb-3">Generated clips</h3>
          <div className="grid grid-cols-5 gap-3">
            {outputs.map(p => (
              <button key={p} onClick={() => window.api.app.showItem(p)} className="border border-line rounded overflow-hidden bg-bg hover:border-blood/40">
                <video src={fileUrl(p)} className="w-full aspect-[9/16] object-cover" muted />
                <div className="text-[10px] text-muted p-1 truncate font-mono text-center">{p.split(/[\\/]/).pop()}</div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
