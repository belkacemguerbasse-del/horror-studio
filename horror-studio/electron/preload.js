const { contextBridge, ipcRenderer } = require('electron');

const invoke = (channel, ...args) => ipcRenderer.invoke(channel, ...args);
const on = (channel, cb) => {
  const fn = (_e, ...args) => cb(...args);
  ipcRenderer.on(channel, fn);
  return () => ipcRenderer.removeListener(channel, fn);
};

contextBridge.exposeInMainWorld('api', {
  episodes: {
    list:    ()        => invoke('episodes:list'),
    get:     (id)      => invoke('episodes:get', id),
    create:  (data)    => invoke('episodes:create', data),
    update:  (id, p)   => invoke('episodes:update', id, p),
    remove:  (id)      => invoke('episodes:remove', id),
    importImages: (id, paths) => invoke('episodes:importImages', id, paths),
    importSlices: (id, dataUrls) => invoke('episodes:importSlices', id, dataUrls),
    listFrames:   (id)        => invoke('episodes:listFrames', id),
    listOutputs:  (id)        => invoke('episodes:listOutputs', id),
    readFile:     (path)      => invoke('episodes:readFile', path),
    writeJSON:    (id, name, data) => invoke('episodes:writeJSON', id, name, data)
  },
  settings: {
    get: ()    => invoke('settings:get'),
    set: (p)   => invoke('settings:set', p)
  },
  comfyui: {
    ping: (url) => invoke('comfyui:ping', url)
  },
  pipeline: {
    generate:   (id, opts) => invoke('pipeline:generate', id, opts),
    concat:     (id, opts) => invoke('pipeline:concat', id, opts),
    cancel:     (jobId)    => invoke('pipeline:cancel', jobId),
    onLog:      (cb)       => on('pipeline:log', cb),
    onProgress: (cb)       => on('pipeline:progress', cb),
    onDone:     (cb)       => on('pipeline:done', cb)
  },
  elevenlabs: {
    voices:   (key)              => invoke('eleven:voices', key),
    generate: (id, opts)         => invoke('eleven:generate', id, opts)
  },
  app: {
    openPath:        (p)    => invoke('app:openPath', p),
    showItem:        (p)    => invoke('app:showItem', p),
    pickFiles:       (o)    => invoke('app:pickFiles', o),
    pickDir:         ()     => invoke('app:pickDir'),
    copyToClipboard: (t)    => invoke('app:copyToClipboard', t),
    appPath:         ()     => invoke('app:appPath'),
    readFileAsDataUrl: (p)  => invoke('app:readFileAsDataUrl', p)
  }
});
