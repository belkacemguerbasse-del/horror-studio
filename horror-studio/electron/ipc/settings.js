const path = require('path');
const Store = require('electron-store');

const store = new Store({
  name: 'settings',
  defaults: {
    comfyUrl: 'http://127.0.0.1:8000',
    projectsRoot: path.resolve(__dirname, '..', '..', '..', 'projects'),
    workflowApiPath: path.resolve(__dirname, '..', '..', '..', 'video_ltx2_3_i2v_api.json'),
    pythonExe: 'python',
    ffmpegPath: '',
    voiceVolume: 1.10,
    ambientVolume: 0.25,
    generateScript: path.resolve(__dirname, '..', '..', '..', 'generate_batch.py'),
    concatScript:   path.resolve(__dirname, '..', '..', '..', 'concat_final.py'),
    elevenApiKey: '',
    elevenVoiceId: '',
    elevenModelId: 'eleven_multilingual_v2',
    elevenLanguage: 'auto',
    elevenUseStitching: true,
    defaultFps: 25,
    defaultWidth: 720,
    defaultHeight: 1280,
    defaultDuration: 7,
    visualStyle: `Stop-motion animation aesthetic in the style of Laika Studios (Coraline, ParaNorman, Boxtrolls) crossed with Tim Burton (Corpse Bride, Frankenweenie, Nightmare Before Christmas) and Guillermo del Toro's Pinocchio.

Character design:
- Stylized 3D-rendered puppet characters with handcrafted felt-and-clay surface texture
- Oversized expressive eyes (roughly 1.5× normal proportion), anime-influenced almond shape, with visible iris detail and catch-lights
- Tiny pointed nose, small delicate mouth (almost always closed)
- Elongated slender neck, narrow shoulders, slim wrists
- Porcelain pale skin with cool blue-green undertones, subtle freckles or sculpted skin imperfections
- Female protagonist: dark hair pulled back tightly in a low bun, wisps at the temples
- Wardrobe: Victorian / Edwardian period — high-collared dark dresses, lace cuffs, button-up bodices, long sleeves, ankle-length skirts

Lighting & color:
- Low-key cinematic gothic horror lighting
- DOMINANT cool desaturated teal-blue / slate-blue from windows, moonlight, and ambient sources
- WARM dirty amber / candlelight accents from oil lamps, candles, fireplaces — small pools of warmth in a cold scene
- Deep pure-black shadows, never lifted, never gray
- Volumetric atmospheric fog drifting through interiors
- Strict desaturated palette: muted teal, cold slate blue, antique amber, charcoal black, ivory highlights
- ABSOLUTELY NO saturated colors, no neon, no pure white, no modern bright tones

Environment:
- Gothic architecture: pointed arch windows with leaded glass panes, carved stone walls, dark wood paneling, ornate wrought-iron details
- Victorian/Edwardian interior clutter: candelabras, leather-bound sketchbooks, quill pens, antique furniture, dripping wax, dust
- Carved wooden staircases with worn banisters
- Soft painterly depth of field, slight cinematic anamorphic distortion at the edges
- 35mm grain texture overlay subtle but visible

Forbidden:
- Modern clothing, electronics, plastic-looking surfaces
- Saturated or neon colors
- Cartoonish 2D anime look, Disney-style soft pastel
- Photorealistic real-world humans — keep the puppet stylization always`
  }
});

// Backfill missing defaults for users who created the store before new keys were added
function backfillDefaults() {
  const defaults = store.store && store.store.__defaults;
  const initial = {
    visualStyle: store.get('visualStyle'),
    elevenModelId: store.get('elevenModelId'),
    elevenLanguage: store.get('elevenLanguage'),
    elevenUseStitching: store.get('elevenUseStitching')
  };
  // electron-store returns the default on .get() if the key is missing, but
  // doesn't persist it until set. Force persist so it appears in store.store.
  for (const [k, v] of Object.entries(initial)) {
    if (!store.has(k) && v != null) store.set(k, v);
  }
}
backfillDefaults();

function register(ipcMain) {
  ipcMain.handle('settings:get', () => store.store);
  ipcMain.handle('settings:set', (_e, patch) => {
    Object.entries(patch || {}).forEach(([k, v]) => store.set(k, v));
    return store.store;
  });
}

module.exports = { register, store };
