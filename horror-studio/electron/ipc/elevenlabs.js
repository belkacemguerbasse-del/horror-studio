const fs = require('fs');
const path = require('path');
const { Agent } = require('undici');
const { store } = require('./settings');

const BASE = 'https://api.elevenlabs.io/v1';

// Force IPv4 + longer connect/read timeouts. Windows networking + Node's IPv6
// happy-eyeballs often cause spurious ConnectTimeoutError on api.elevenlabs.io.
const ipv4Dispatcher = new Agent({
  connect: { family: 4, timeout: 30_000 },
  bodyTimeout: 120_000,
  headersTimeout: 30_000
});

async function fetchJSON(url, opts = {}) {
  const r = await fetchWithRetry(url, opts, {
    tries: 3,
    onRetry: ({ attempt, code, wait }) => console.log(`[ElevenLabs] ${url} retry ${attempt}/3 after ${code} — waiting ${wait}ms`)
  });
  if (!r.ok) {
    const text = await r.text().catch(() => '');
    let hint = '';
    if (r.status === 401) hint = ' — check the key has no leading/trailing space, is not revoked, and has the text_to_speech permission';
    throw new Error(`ElevenLabs ${r.status}: ${text || r.statusText}${hint}`);
  }
  return r.json();
}

function wrappedFetch(url, opts = {}) {
  return fetch(url, { ...opts, dispatcher: ipv4Dispatcher });
}

// Retry a fetch up to `tries` times on transient network errors.
// Exponential backoff: 1s, 3s, 7s.
const TRANSIENT_CODES = new Set([
  'UND_ERR_CONNECT_TIMEOUT',
  'UND_ERR_SOCKET',
  'UND_ERR_HEADERS_TIMEOUT',
  'UND_ERR_BODY_TIMEOUT',
  'ETIMEDOUT',
  'ECONNRESET',
  'EAI_AGAIN'
]);

async function fetchWithRetry(url, opts, { tries = 3, onRetry } = {}) {
  let lastErr;
  for (let attempt = 1; attempt <= tries; attempt++) {
    try {
      return await wrappedFetch(url, opts);
    } catch (e) {
      const code = e?.cause?.code || e?.code || '';
      lastErr = e;
      if (!TRANSIENT_CODES.has(code) || attempt === tries) throw e;
      const wait = (2 ** attempt - 1) * 1000; // 1s, 3s, 7s
      if (onRetry) onRetry({ attempt, code, wait });
      await new Promise(r => setTimeout(r, wait));
    }
  }
  throw lastErr;
}

function register(ipcMain) {
  ipcMain.handle('eleven:voices', async (_e, key) => {
    const apiKey = (key || store.get('elevenApiKey') || '').trim();
    if (!apiKey) throw new Error('Missing ElevenLabs API key (Settings)');
    try {
      const data = await fetchJSON(`${BASE}/voices`, { headers: { 'xi-api-key': apiKey } });
      return data.voices.map(v => ({
        voice_id: v.voice_id,
        name: v.name,
        labels: v.labels,
        preview_url: v.preview_url
      }));
    } catch (e) {
      const code = e?.cause?.code || e?.code || '';
      if (code === 'UND_ERR_CONNECT_TIMEOUT' || code === 'ENOTFOUND' || code === 'ECONNREFUSED') {
        throw new Error(`Network error loading voices (${code}) — could not reach api.elevenlabs.io. Check internet/firewall/VPN. If on a corporate network, set HTTPS_PROXY env var before launching the app.`);
      }
      throw e;
    }
  });

  ipcMain.handle('eleven:generate', async (_e, episodeId, opts) => {
    const apiKey = (store.get('elevenApiKey') || '').trim();
    if (!apiKey) throw new Error('Missing ElevenLabs API key (Settings)');

    const voiceId = opts.voiceId || store.get('elevenVoiceId');
    if (!voiceId) throw new Error('Missing voice id');

    const projectsRoot = store.get('projectsRoot');
    const outDir = path.join(projectsRoot, episodeId, 'voice');
    fs.mkdirSync(outDir, { recursive: true });

    const lines        = opts.lines || [];
    const modelId      = opts.modelId      || store.get('elevenModelId')   || 'eleven_multilingual_v2';
    const language     = opts.language     || store.get('elevenLanguage')  || 'auto';
    let   useStitching = opts.useStitching ?? store.get('elevenUseStitching') ?? true;
    // v3 does not yet support previous_text/next_text stitching
    if (modelId === 'eleven_v3') useStitching = false;

    const results = [];
    let totalChars = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const body = {
        text: line.text,
        model_id: modelId,
        voice_settings: {
          stability: opts.stability ?? 0.55,
          similarity_boost: opts.similarity ?? 0.75,
          style: opts.style ?? 0.45,
          use_speaker_boost: true
        }
      };

      // Stitching: pass the surrounding lines for tonal continuity
      if (useStitching) {
        const prev = lines[i - 1]?.text;
        const next = lines[i + 1]?.text;
        if (prev) body.previous_text = prev;
        if (next) body.next_text = next;
      }

      // Language enforcement (only valid on multilingual models)
      if (language && language !== 'auto') {
        body.language_code = language;
      }

      let r;
      try {
        r = await fetchWithRetry(`${BASE}/text-to-speech/${voiceId}`, {
          method: 'POST',
          headers: {
            'xi-api-key': apiKey,
            'Content-Type': 'application/json',
            'Accept': 'audio/mpeg'
          },
          body: JSON.stringify(body)
        }, {
          tries: 3,
          onRetry: ({ attempt, code, wait }) => {
            console.log(`[ElevenLabs] line ${line.id} retry ${attempt}/3 after ${code} — waiting ${wait}ms`);
          }
        });
      } catch (netErr) {
        const code = netErr?.cause?.code || netErr?.code || '';
        const hint = (code === 'UND_ERR_CONNECT_TIMEOUT' || code === 'ETIMEDOUT')
          ? ' — could not reach api.elevenlabs.io after 3 retries. Check internet/firewall/VPN. If on a corporate network, set HTTPS_PROXY env var before launching the app.'
          : '';
        throw new Error(`Network error on line ${line.id} (${code || netErr.message})${hint}`);
      }
      if (!r.ok) {
        const text = await r.text().catch(() => '');
        throw new Error(`TTS line ${line.id}: ${r.status} ${text}`);
      }

      const chars = parseInt(r.headers.get('character-cost') || r.headers.get('x-character-count') || '0', 10) || line.text.length;
      totalChars += chars;

      const buf = Buffer.from(await r.arrayBuffer());
      const out = path.join(outDir, `${line.id}.mp3`);
      fs.writeFileSync(out, buf);
      results.push({
        id: line.id,
        file: out,
        bytes: buf.length,
        chars,
        stitched: useStitching && (i > 0 || i < lines.length - 1)
      });
    }

    return { results, totalChars, modelId, language, useStitching };
  });
}

module.exports = { register };
