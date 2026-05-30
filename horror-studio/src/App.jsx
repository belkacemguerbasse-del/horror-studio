import { useEffect } from 'react';
import { useStore } from './lib/store.js';
import Sidebar from './components/Sidebar.jsx';
import Dashboard from './components/Dashboard.jsx';
import EpisodeDetail from './components/EpisodeDetail.jsx';
import Settings from './components/Settings.jsx';

export default function App() {
  const view = useStore(s => s.view);
  const refreshSettings = useStore(s => s.refreshSettings);
  const refreshEpisodes = useStore(s => s.refreshEpisodes);
  const pingComfy = useStore(s => s.pingComfy);
  const appendJobLog = useStore(s => s.appendJobLog);
  const finishJob = useStore(s => s.finishJob);

  useEffect(() => {
    (async () => {
      await refreshSettings();
      await refreshEpisodes();
      await pingComfy();
    })();
    const interval = setInterval(() => pingComfy(), 15000);

    const offLog = window.api.pipeline.onLog(({ episodeId, jobId, chunk }) => {
      appendJobLog(episodeId, jobId, chunk);
    });
    const offDone = window.api.pipeline.onDone(({ episodeId, code, kind }) => {
      finishJob(episodeId, code);
      refreshEpisodes();
    });

    return () => { clearInterval(interval); offLog(); offDone(); };
  }, []);

  return (
    <div className="h-full w-full flex bg-bg text-text">
      <Sidebar />
      <main className="flex-1 overflow-hidden flex flex-col">
        {view === 'dashboard' && <Dashboard />}
        {view === 'episode'   && <EpisodeDetail />}
        {view === 'settings'  && <Settings />}
      </main>
    </div>
  );
}
