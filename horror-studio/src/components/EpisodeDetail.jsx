import { useState } from 'react';
import { useStore } from '../lib/store.js';
import { statusBadge, relativeDate } from '../lib/status.js';
import StepStory     from './steps/StepStory.jsx';
import StepImages    from './steps/StepImages.jsx';
import StepPrompts   from './steps/StepPrompts.jsx';
import StepGenerate  from './steps/StepGenerate.jsx';
import StepVoice     from './steps/StepVoice.jsx';
import StepConcat    from './steps/StepConcat.jsx';
import StepPost      from './steps/StepPost.jsx';

const STEPS = [
  { id: 'story',    label: '1. Story & Banana prompt', component: StepStory },
  { id: 'images',   label: '2. Import storyboard',      component: StepImages },
  { id: 'prompts',  label: '3. Motion prompts',         component: StepPrompts },
  { id: 'generate', label: '4. Generate videos',        component: StepGenerate },
  { id: 'voice',    label: '5. Voice-over',             component: StepVoice },
  { id: 'concat',   label: '6. Final concat',           component: StepConcat },
  { id: 'post',     label: '7. Publish & track',        component: StepPost }
];

export default function EpisodeDetail() {
  const selected = useStore(s => s.selected);
  const removeEpisode = useStore(s => s.removeEpisode);
  const [stepId, setStepId] = useState('story');

  if (!selected) return <div className="p-10 text-muted">Loading episode…</div>;

  const { meta, paths } = selected;
  const s = statusBadge(meta.status);
  const Step = STEPS.find(x => x.id === stepId).component;

  return (
    <div className="flex-1 overflow-hidden flex flex-col">
      <header className="px-8 py-5 border-b border-line flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-xl font-semibold truncate">{meta.title}</h1>
            <span className={`badge ${s.color}`}>{s.label}</span>
          </div>
          <div className="text-xs text-muted">
            {relativeDate(meta.scheduledFor)} · {meta.scheduledFor} · <span className="font-mono">{meta.id}</span>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button onClick={() => window.api.app.openPath(paths.root)} className="btn">📂 Open folder</button>
          <button onClick={async () => {
            if (confirm(`Delete "${meta.title}" and all its files? This cannot be undone.`)) {
              await removeEpisode(meta.id);
            }
          }} className="btn text-red-400 hover:bg-red-950/40">Delete</button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <nav className="w-64 shrink-0 border-r border-line bg-panel py-3 px-2 space-y-0.5 overflow-y-auto">
          {STEPS.map(st => (
            <button key={st.id} onClick={() => setStepId(st.id)}
              className={`w-full text-left px-3 py-2 rounded-md text-sm ${stepId === st.id ? 'bg-card text-text' : 'text-ghost hover:bg-card'}`}>
              {st.label}
            </button>
          ))}
        </nav>
        <div className="flex-1 overflow-y-auto p-8">
          <Step episode={selected} />
        </div>
      </div>
    </div>
  );
}
