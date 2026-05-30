export const STATUSES = {
  draft:       { label: 'Draft',       color: 'border-line text-muted bg-card' },
  storyboard:  { label: 'Storyboard',  color: 'border-amber-700/50 text-amber-400 bg-amber-950/30' },
  prompts:     { label: 'Prompts OK',  color: 'border-sky-700/50 text-sky-400 bg-sky-950/30' },
  generating:  { label: 'Generating',  color: 'border-violet-700/50 text-violet-400 bg-violet-950/30 animate-pulse' },
  ready:       { label: 'Ready',       color: 'border-emerald-700/50 text-emerald-400 bg-emerald-950/30' },
  posted:      { label: 'Posted',      color: 'border-rust/50 text-rust bg-rust/10' }
};

export function statusBadge(status) {
  return STATUSES[status] || STATUSES.draft;
}

export function todayISO() { return new Date().toISOString().slice(0, 10); }

export function relativeDate(iso) {
  if (!iso) return '';
  const today = todayISO();
  if (iso === today) return 'Today';
  const t = new Date(today);
  const d = new Date(iso);
  const diff = Math.round((d - t) / 86400000);
  if (diff === 1) return 'Tomorrow';
  if (diff === -1) return 'Yesterday';
  if (diff > 1 && diff <= 7) return `In ${diff}d`;
  if (diff < -1 && diff >= -7) return `${-diff}d ago`;
  return iso;
}
