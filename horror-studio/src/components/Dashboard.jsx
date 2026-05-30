import { useMemo, useState } from 'react';
import { useStore } from '../lib/store.js';
import { statusBadge, todayISO, relativeDate } from '../lib/status.js';
import NewEpisodeModal from './NewEpisodeModal.jsx';

export default function Dashboard() {
  const { episodes, selectEpisode } = useStore();
  const [showNew, setShowNew] = useState(false);

  const today = todayISO();
  const stats = useMemo(() => {
    const total = episodes.length;
    const posted = episodes.filter(e => e.posted).length;
    const ready = episodes.filter(e => e.status === 'ready').length;
    const todayEp = episodes.find(e => e.scheduledFor === today);
    return { total, posted, ready, todayEp };
  }, [episodes, today]);

  return (
    <div className="flex-1 overflow-y-auto">
      <header className="px-8 py-6 border-b border-line flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-muted text-sm">{episodes.length} episode{episodes.length > 1 ? 's' : ''} · {today}</p>
        </div>
        <button onClick={() => setShowNew(true)} className="btn-primary">+ New episode</button>
      </header>

      <section className="px-8 py-6 grid grid-cols-4 gap-4">
        <Stat label="Total"     value={stats.total}   />
        <Stat label="Posted"    value={stats.posted}  />
        <Stat label="Ready"     value={stats.ready}   tone="emerald" />
        <Stat label="Today"     value={stats.todayEp ? stats.todayEp.title : '—'} small />
      </section>

      <section className="px-8 pb-10">
        <h2 className="text-sm uppercase tracking-wider text-muted mb-3">All episodes</h2>
        {episodes.length === 0 ? (
          <div className="card p-10 text-center">
            <div className="text-4xl mb-3">🎬</div>
            <div className="text-text font-medium mb-1">No episodes yet</div>
            <div className="text-muted text-sm mb-4">Create your first daily horror episode to get started.</div>
            <button onClick={() => setShowNew(true)} className="btn-primary">+ New episode</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {episodes.map(ep => <EpisodeCard key={ep.id} ep={ep} onOpen={() => selectEpisode(ep.id)} />)}
          </div>
        )}
      </section>

      {showNew && <NewEpisodeModal onClose={() => setShowNew(false)} />}
    </div>
  );
}

function Stat({ label, value, small, tone }) {
  return (
    <div className="card p-4">
      <div className="label mb-1">{label}</div>
      <div className={`font-semibold ${small ? 'text-base truncate' : 'text-3xl'} ${tone==='emerald'?'text-emerald-400':''}`}>{value}</div>
    </div>
  );
}

function EpisodeCard({ ep, onOpen }) {
  const s = statusBadge(ep.status);
  return (
    <button onClick={onOpen} className="card p-4 text-left hover:border-blood/40 transition group">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="min-w-0">
          <div className="font-semibold text-text truncate group-hover:text-white">{ep.title}</div>
          <div className="text-xs text-muted">{relativeDate(ep.scheduledFor)} · {ep.scheduledFor}</div>
        </div>
        <span className={`badge ${s.color}`}>{s.label}</span>
      </div>
      {ep.storyIntent && <div className="text-xs text-ghost line-clamp-2">{ep.storyIntent}</div>}
      {ep.tiktokUrl && <div className="text-xs text-rust mt-2 truncate">📱 {ep.tiktokUrl}</div>}
    </button>
  );
}
