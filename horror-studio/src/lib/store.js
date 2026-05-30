import { create } from 'zustand';

export const useStore = create((set, get) => ({
  episodes: [],
  selectedId: null,
  selected: null,
  settings: null,
  comfyStatus: { ok: false, error: 'unchecked' },
  view: 'dashboard', // dashboard | episode | settings
  jobs: {}, // episodeId -> { jobId, kind, logs: [], done: false, code: null }

  setView: (view) => set({ view }),

  refreshSettings: async () => {
    const settings = await window.api.settings.get();
    set({ settings });
    return settings;
  },

  saveSettings: async (patch) => {
    const settings = await window.api.settings.set(patch);
    set({ settings });
    return settings;
  },

  pingComfy: async () => {
    const s = get().settings;
    if (!s) return;
    const status = await window.api.comfyui.ping(s.comfyUrl);
    set({ comfyStatus: status });
    return status;
  },

  refreshEpisodes: async () => {
    const episodes = await window.api.episodes.list();
    set({ episodes });
    const id = get().selectedId;
    if (id) {
      const selected = await window.api.episodes.get(id);
      set({ selected });
    }
    return episodes;
  },

  selectEpisode: async (id) => {
    if (!id) { set({ selectedId: null, selected: null, view: 'dashboard' }); return; }
    set({ selectedId: id, view: 'episode' });
    const selected = await window.api.episodes.get(id);
    set({ selected });
  },

  createEpisode: async (data) => {
    const ep = await window.api.episodes.create(data);
    await get().refreshEpisodes();
    await get().selectEpisode(ep.id);
    return ep;
  },

  updateEpisode: async (id, patch) => {
    await window.api.episodes.update(id, patch);
    await get().refreshEpisodes();
  },

  removeEpisode: async (id) => {
    await window.api.episodes.remove(id);
    if (get().selectedId === id) set({ selectedId: null, selected: null, view: 'dashboard' });
    await get().refreshEpisodes();
  },

  appendJobLog: (episodeId, jobId, chunk, kind) => set(s => {
    const j = s.jobs[episodeId] || { jobId, kind, logs: [], done: false, code: null };
    return { jobs: { ...s.jobs, [episodeId]: { ...j, jobId, kind: kind || j.kind, logs: [...j.logs, chunk] } } };
  }),
  finishJob: (episodeId, code) => set(s => {
    const j = s.jobs[episodeId];
    if (!j) return {};
    return { jobs: { ...s.jobs, [episodeId]: { ...j, done: true, code } } };
  }),
  clearJob: (episodeId) => set(s => {
    const { [episodeId]: _, ...rest } = s.jobs;
    return { jobs: rest };
  })
}));
