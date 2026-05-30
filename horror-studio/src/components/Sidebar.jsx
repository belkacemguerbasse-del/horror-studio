import { useStore } from '../lib/store.js';
import { statusBadge, relativeDate, todayISO } from '../lib/status.js';

export default function Sidebar() {
  const { episodes, view, selectedId, setView, selectEpisode, comfyStatus, settings } = useStore();

  const today = todayISO();
  const upcoming = episodes.filter(e => e.scheduledFor >= today).slice().reverse();
  const past     = episodes.filter(e => e.scheduledFor < today);

  return (
    <aside className="w-72 shrink-0 bg-panel border-r border-line flex flex-col">
      <div className="p-4 border-b border-line">
        <button onClick={() => { selectEpisode(null); setView('dashboard'); }} className="flex items-center gap-2 group">
          <span className="text-2xl">🎬</span>
          <div>
            <div className="text-text font-semibold leading-tight">Horror Studio</div>
            <div className="text-xs text-muted">Daily TikTok pipeline</div>
          </div>
        </button>
      </div>

      <nav className="p-3 space-y-1">
        <button onClick={() => { selectEpisode(null); setView('dashboard'); }}
          className={`w-full text-left px-3 py-2 rounded-md text-sm flex items-center gap-2 ${view==='dashboard' ? 'bg-card text-text' : 'text-ghost hover:bg-card'}`}>
          <span>📅</span> Dashboard
        </button>
        <button onClick={() => { selectEpisode(null); setView('settings'); }}
          className={`w-full text-left px-3 py-2 rounded-md text-sm flex items-center gap-2 ${view==='settings' ? 'bg-card text-text' : 'text-ghost hover:bg-card'}`}>
          <span>⚙️</span> Settings
        </button>
      </nav>

      <div className="px-4 pt-3 pb-1 text-xs uppercase tracking-wider text-muted">Upcoming</div>
      <div className="px-2 space-y-0.5 overflow-y-auto max-h-[35vh]">
        {upcoming.length === 0 && <div className="px-3 py-2 text-xs text-muted italic">No upcoming episodes</div>}
        {upcoming.map(ep => <EpisodeRow key={ep.id} ep={ep} active={selectedId === ep.id} onClick={() => selectEpisode(ep.id)} />)}
      </div>

      <div className="px-4 pt-3 pb-1 text-xs uppercase tracking-wider text-muted">Past</div>
      <div className="px-2 space-y-0.5 overflow-y-auto flex-1">
        {past.length === 0 && <div className="px-3 py-2 text-xs text-muted italic">No past episodes</div>}
        {past.map(ep => <EpisodeRow key={ep.id} ep={ep} active={selectedId === ep.id} onClick={() => selectEpisode(ep.id)} />)}
      </div>

      <div className="p-3 border-t border-line text-xs">
        <div className="flex items-center gap-2 text-muted">
          <span className={`w-2 h-2 rounded-full ${comfyStatus.ok ? 'bg-emerald-500' : 'bg-red-500'}`} />
          <span>ComfyUI {comfyStatus.ok ? 'online' : 'offline'}</span>
        </div>
        <div className="text-muted truncate">{settings?.comfyUrl}</div>
      </div>
    </aside>
  );
}

function EpisodeRow({ ep, active, onClick }) {
  const s = statusBadge(ep.status);
  return (
    <button onClick={onClick}
      className={`w-full text-left px-3 py-2 rounded-md text-sm group transition ${active ? 'bg-card' : 'hover:bg-card'}`}>
      <div className="flex items-center justify-between gap-2">
        <div className="truncate font-medium text-text">{ep.title}</div>
        <span className={`badge ${s.color} text-[10px]`}>{s.label}</span>
      </div>
      <div className="text-xs text-muted">{relativeDate(ep.scheduledFor)}</div>
    </button>
  );
}
